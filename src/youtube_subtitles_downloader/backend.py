"""Cross-platform yt-dlp/ffmpeg discovery and subprocess helpers."""

from __future__ import annotations

import functools
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Sequence

from .resources import resource_path


class ToolNotFoundError(RuntimeError):
    """Raised when a required external tool cannot be located."""

    def __init__(self, tool: str) -> None:
        self.tool = tool
        super().__init__(f"{tool} was not found.\n\n{install_hint(tool)}")


def install_hint(tool: str) -> str:
    """Return platform-specific installation instructions."""
    if sys.platform == "darwin":
        if tool == "yt-dlp":
            return "Install it with: brew install yt-dlp"
        return "Install it with: brew install ffmpeg"

    if os.name == "nt":
        if tool == "yt-dlp":
            return "Install it with: winget install yt-dlp.yt-dlp"
        return "Install it with: winget install Gyan.FFmpeg"

    if tool == "yt-dlp":
        return (
            "Install it with: python3 -m pip install --user -U yt-dlp "
            "(or use your package manager)"
        )
    return "Install it with: sudo apt install ffmpeg (or use your package manager)"


def _tool_names(name: str) -> list[str]:
    if os.name == "nt":
        return [f"{name}.exe", name]
    return [name]


def _candidate_roots() -> list[Path]:
    roots: list[Path] = []

    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            roots.append(Path(meipass))
        executable_dir = Path(sys.executable).resolve().parent
        roots.extend([executable_dir, executable_dir.parent / "Resources"])
    else:
        roots.append(resource_path())

    roots.append(resource_path("vendor"))

    unique: list[Path] = []
    for root in roots:
        try:
            resolved = root.resolve()
        except OSError:
            resolved = root
        if resolved not in unique:
            unique.append(resolved)
    return unique


def _common_tool_dirs() -> list[Path]:
    home = Path.home()
    dirs: list[Path] = [home / ".local" / "bin", home / "bin"]

    if os.name == "nt":
        local_app_data = Path(
            os.environ.get("LOCALAPPDATA", home / "AppData" / "Local")
        )
        roaming_app_data = Path(
            os.environ.get("APPDATA", home / "AppData" / "Roaming")
        )
        program_files = Path(
            os.environ.get("ProgramFiles", "C:/Program Files")
        )
        program_files_x86 = Path(
            os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")
        )

        dirs.extend(
            [
                local_app_data / "Microsoft" / "WinGet" / "Links",
                local_app_data / "Programs" / "Python" / "Scripts",
                roaming_app_data / "Python" / "Scripts",
                home / "scoop" / "shims",
                program_files / "yt-dlp",
                program_files / "ffmpeg" / "bin",
                program_files_x86 / "yt-dlp",
                Path("C:/ProgramData/chocolatey/bin"),
            ]
        )

        for base in (
            local_app_data / "Programs" / "Python",
            program_files,
            program_files_x86,
        ):
            try:
                for child in base.glob("Python*/Scripts"):
                    dirs.append(child)
            except OSError:
                pass
    else:
        dirs.extend(
            [
                Path("/opt/homebrew/bin"),
                Path("/usr/local/bin"),
                Path("/usr/bin"),
                Path("/bin"),
                Path("/snap/bin"),
                Path("/var/lib/flatpak/exports/bin"),
                home / ".pyenv" / "shims",
            ]
        )

    return dirs


def find_tool(name: str, env_var: str) -> Path | None:
    """Locate a tool in bundled resources, PATH, or common install folders."""
    candidates: list[Path] = []

    env_value = os.environ.get(env_var)
    if env_value:
        candidates.append(
            Path(os.path.expanduser(os.path.expandvars(env_value)))
        )

    for root in _candidate_roots():
        for exe_name in _tool_names(name):
            candidates.append(root / "bin" / exe_name)
            candidates.append(root / exe_name)

    for exe_name in _tool_names(name):
        located = shutil.which(exe_name)
        if located:
            candidates.append(Path(located))

    for directory in _common_tool_dirs():
        for exe_name in _tool_names(name):
            candidates.append(directory / exe_name)

    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)

        try:
            if not candidate.is_file():
                continue
            if os.name != "nt" and not os.access(candidate, os.X_OK):
                continue
            return candidate.resolve()
        except OSError:
            continue

    return None


@functools.lru_cache(maxsize=1)
def find_ytdlp() -> Path | None:
    """Return the yt-dlp executable, preferring a bundled copy."""
    return find_tool("yt-dlp", "YTDLP_PATH")


@functools.lru_cache(maxsize=1)
def find_ffmpeg() -> Path | None:
    """Return the ffmpeg executable, preferring a bundled copy."""
    return find_tool("ffmpeg", "FFMPEG_PATH")


def require_ffmpeg() -> Path:
    """Return ffmpeg or raise a helpful ToolNotFoundError."""
    ffmpeg = find_ffmpeg()
    if ffmpeg is None:
        raise ToolNotFoundError("ffmpeg")
    return ffmpeg


def build_subprocess_env() -> dict[str, str]:
    """Build an environment that works for Finder/Explorer-launched apps."""
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")

    path_entries: list[str] = []
    for tool in (find_ytdlp(), find_ffmpeg()):
        if tool is not None:
            path_entries.append(str(tool.parent))

    path_entries.extend(str(directory) for directory in _common_tool_dirs())
    current_path = env.get("PATH", "")
    if current_path:
        path_entries.append(current_path)

    seen: set[str] = set()
    unique_entries: list[str] = []
    for entry in path_entries:
        if entry and entry not in seen:
            seen.add(entry)
            unique_entries.append(entry)

    env["PATH"] = os.pathsep.join(unique_entries)
    return env


def subprocess_creation_kwargs() -> dict[str, int]:
    """Prevent console windows from flashing on Windows."""
    if os.name == "nt":
        return {
            "creationflags": getattr(subprocess, "CREATE_NO_WINDOW", 0)
        }
    return {}


def run_ytdlp(
    args: Sequence[str], timeout: int | None = None
) -> subprocess.CompletedProcess[str]:
    """Run yt-dlp safely with an argument list and a UTF-8 environment."""
    ytdlp = find_ytdlp()
    if ytdlp is None:
        raise ToolNotFoundError("yt-dlp")

    command = [str(ytdlp), "--no-colors", *(str(arg) for arg in args)]
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
        env=build_subprocess_env(),
        **subprocess_creation_kwargs(),
    )


def process_error(
    completed: subprocess.CompletedProcess[str], fallback: str
) -> str:
    """Build a useful error message from a completed yt-dlp process."""
    detail = (completed.stderr or "").strip()
    if not detail:
        detail = (completed.stdout or "").strip()
    if not detail:
        detail = fallback
    if len(detail) > 4000:
        detail = detail[-4000:]
    return detail


def parse_metadata(stdout: str) -> dict | None:
    """Parse the last JSON object emitted by yt-dlp --dump-json."""
    for line in reversed(stdout.splitlines()):
        candidate = line.strip()
        if not candidate:
            continue
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    return None
