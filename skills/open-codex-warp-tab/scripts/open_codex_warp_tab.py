#!/usr/bin/env python3
"""Open a visible Codex CLI session through a Warp Tab Config."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import platform
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import quote


COLORS = (
    "black",
    "red",
    "green",
    "yellow",
    "blue",
    "magenta",
    "cyan",
    "white",
)
DEFAULT_CONFIG_NAME = "codex_session_launcher"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create a Warp Tab Config that starts an interactive Codex session "
            "and open it in the active Warp window."
        )
    )
    parser.add_argument("prompt", help="Prompt to submit to the new Codex session.")
    parser.add_argument(
        "-C",
        "--directory",
        default=os.getcwd(),
        help="Codex working directory. Defaults to the current directory.",
    )
    parser.add_argument(
        "--title",
        help="Visible Warp tab title. Defaults to the prompt's first line.",
    )
    parser.add_argument(
        "--color",
        choices=COLORS,
        default="cyan",
        help="Warp tab color. Default: cyan.",
    )
    parser.add_argument(
        "--config-name",
        default=DEFAULT_CONFIG_NAME,
        help=f"Warp Tab Config file stem. Default: {DEFAULT_CONFIG_NAME}.",
    )
    parser.add_argument(
        "--config-dir",
        type=Path,
        help="Override Warp's Tab Config directory, primarily for tests.",
    )
    parser.add_argument(
        "--new-window",
        action="store_true",
        help="Open a separate Warp window instead of the active window/group.",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="Write the Tab Config but do not open Warp.",
    )
    parser.add_argument(
        "--print-only",
        action="store_true",
        help="Print the generated config and URI without writing or opening.",
    )
    return parser.parse_args()


def default_config_dir(system: str) -> Path:
    home = Path.home()
    if system == "Darwin":
        return home / ".warp" / "tab_configs"
    if system == "Linux":
        data_home = Path(os.environ.get("XDG_DATA_HOME", home / ".local" / "share"))
        return data_home / "warp-terminal" / "tab_configs"
    if system == "Windows":
        appdata = os.environ.get("APPDATA")
        if not appdata:
            raise RuntimeError("APPDATA is required to locate Warp Tab Configs.")
        return Path(appdata) / "warp" / "Warp" / "data" / "tab_configs"
    raise RuntimeError(f"Unsupported platform for Warp Tab Configs: {system}")


def toml_string(value: str) -> str:
    """Return a TOML-compatible basic string."""
    return json.dumps(value, ensure_ascii=False)


def normalized_title(prompt: str, explicit_title: str | None) -> str:
    source = explicit_title or prompt.strip().splitlines()[0]
    compact = re.sub(r"\s+", " ", source).strip()
    if not compact:
        return "New session"
    return compact[:60]


def validate_config_name(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", value):
        raise ValueError(
            "--config-name accepts only letters, digits, underscores, and hyphens."
        )
    return value


def build_config(
    *,
    prompt: str,
    directory: Path,
    title: str,
    color: str,
    system: str,
) -> tuple[str, str]:
    command_parts = ["codex", "-C", str(directory), prompt]
    command = (
        subprocess.list2cmdline(command_parts)
        if system == "Windows"
        else shlex.join(command_parts)
    )
    config = "\n".join(
        (
            'name = "Codex Session Launcher"',
            f"title = {toml_string(f'Codex: {title}')}",
            f'color = "{color}"',
            "",
            "[[panes]]",
            'id = "main"',
            'type = "terminal"',
            f"directory = {toml_string(str(directory))}",
            f"commands = [{toml_string(command)}]",
            "is_focused = true",
            "",
        )
    )
    return config, command


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        delete=False,
    ) as handle:
        handle.write(content)
        temp_path = Path(handle.name)
    temp_path.chmod(0o600)
    os.replace(temp_path, path)


def open_uri(uri: str, system: str) -> None:
    if system == "Darwin":
        subprocess.run(["open", uri], check=True)
        return
    if system == "Linux":
        launcher = shutil.which("xdg-open")
        if not launcher:
            raise RuntimeError("xdg-open is required to open Warp on Linux.")
        subprocess.run([launcher, uri], check=True)
        return
    if system == "Windows":
        os.startfile(uri)  # type: ignore[attr-defined]
        return
    raise RuntimeError(f"Unsupported platform for opening Warp: {system}")


def main() -> int:
    args = parse_args()
    prompt = args.prompt.strip()
    if not prompt:
        print("error: prompt must not be empty", file=sys.stderr)
        return 2

    directory = Path(args.directory).expanduser().resolve()
    if not directory.is_dir():
        print(f"error: directory does not exist: {directory}", file=sys.stderr)
        return 2

    system = platform.system()
    try:
        config_name = validate_config_name(args.config_name)
        config_dir = (
            args.config_dir.expanduser().resolve()
            if args.config_dir
            else default_config_dir(system)
        )
    except (RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    title = normalized_title(prompt, args.title)
    config, command = build_config(
        prompt=prompt,
        directory=directory,
        title=title,
        color=args.color,
        system=system,
    )
    uri = f"warp://tab_config/{quote(config_name)}"
    if args.new_window:
        uri += "?new_window=true"
    config_path = config_dir / f"{config_name}.toml"

    if args.print_only:
        print(config, end="")
        print(f"URI={uri}")
        return 0

    if not shutil.which("codex"):
        print("error: codex executable was not found in PATH", file=sys.stderr)
        return 127

    try:
        atomic_write(config_path, config)
        if not args.no_open:
            open_uri(uri, system)
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"CONFIG={config_path}")
    print(f"URI={uri}")
    print(f"COMMAND={command}")
    print("OPENED=" + ("false" if args.no_open else "true"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
