import os
import sys
import json
from pathlib import Path


def _config_dir() -> Path:
    # When frozen by PyInstaller, write config to %APPDATA% so the EXE
    # doesn't try to write next to itself inside Program Files.
    if getattr(sys, 'frozen', False):
        d = Path(os.environ.get('APPDATA', Path.home())) / 'AstraForge'
        d.mkdir(parents=True, exist_ok=True)
        return d
    return Path(__file__).parent


CONFIG_PATH = _config_dir() / "AstraForge.config.json"


# ============================================================
# CONFIG SYSTEM
# ============================================================

def load_config():
    """Load AstraForge.config.json or return empty defaults."""
    if CONFIG_PATH.exists():
        try:
            with CONFIG_PATH.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_config(cfg):
    """Write updated config back to AstraForge.config.json."""
    with CONFIG_PATH.open("w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def prompt_for_path(label, saved_value=None):
    """
    Prompt the user for a path.
    If a saved value exists, ask for confirmation.
    """
    print(f"\n--- {label} ---")

    if saved_value:
        print(f"Last used path:\n{saved_value}")
        confirm = input("Use this path? (Y/n): ").strip().lower()

        if confirm in ("", "y", "yes"):
            if Path(saved_value).exists():
                return saved_value
            else:
                print("Saved path does not exist anymore. Please enter a new one.")

    # Ask for new path
    while True:
        new_path = input("Enter folder path: ").strip().strip('"')
        if Path(new_path).exists():
            return new_path
        print("Invalid path. Folder does not exist. Try again.")


def get_paths_for_mode(mode):
    """
    Handles prompting + remembering paths for:
    - windows
    - linux
    - diff
    """
    cfg = load_config()

    if mode == "windows":
        raw = prompt_for_path("Windows RAW driver folder",
                              cfg.get("windows_raw"))
        out = prompt_for_path("Windows OUTPUT folder", cfg.get("windows_out"))

        cfg["windows_raw"] = raw
        cfg["windows_out"] = out
        save_config(cfg)

        return raw, out

    if mode == "linux":
        raw = prompt_for_path("Linux RAW driver folder", cfg.get("linux_raw"))
        out = prompt_for_path("Linux OUTPUT folder", cfg.get("linux_out"))

        cfg["linux_raw"] = raw
        cfg["linux_out"] = out
        save_config(cfg)

        return raw, out

    if mode == "diff":
        win_json = prompt_for_path(
            "Windows canonical JSON folder", cfg.get("windows_out"))
        lin_json = prompt_for_path(
            "Linux canonical JSON folder", cfg.get("linux_out"))
        diff_out = prompt_for_path("Diff OUTPUT folder", cfg.get("diff_out"))

        cfg["diff_out"] = diff_out
        save_config(cfg)

        return win_json, lin_json, diff_out

    raise ValueError("Unknown mode")
