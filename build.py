#!/usr/bin/env python3
"""Cross-platform build script for EMS Reporter standalone executable."""

import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SPEC_FILE = PROJECT_ROOT / "EMS_Reporter.spec"
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"


def check_and_install_dependencies():
    """Ensure required packages (PyInstaller, PySide6, pydantic) are installed."""
    print("[1/4] Checking required dependencies...")
    needed = []

    try:
        import PyInstaller
    except ImportError:
        needed.append("pyinstaller")

    try:
        import PySide6
    except ImportError:
        needed.append("PySide6-Essentials")

    try:
        import pydantic
    except ImportError:
        needed.append("pydantic")

    if needed:
        print(f"[INFO] Installing missing packages: {', '.join(needed)}...")
        cmd = [sys.executable, "-m", "pip", "install"] + needed
        res = subprocess.run(cmd)
        if res.returncode != 0:
            print("[ERROR] Failed to install dependencies via pip.")
            return False

    print("[INFO] All required dependencies are present.")
    return True


def clean_previous_builds():
    """Remove previous build/ and dist/ artifacts."""
    print("[2/4] Cleaning previous build artifacts...")
    for d in [BUILD_DIR, DIST_DIR]:
        if d.exists():
            shutil.rmtree(d, ignore_errors=True)
    print("[INFO] Workspace cleaned.")


def run_pyinstaller():
    """Execute PyInstaller with the spec file."""
    print("[3/4] Compiling standalone executable with PyInstaller...")
    if not SPEC_FILE.exists():
        print(f"[ERROR] Spec file not found: {SPEC_FILE}")
        return False

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--clean",
        "--noconfirm",
        str(SPEC_FILE),
    ]

    res = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    if res.returncode != 0:
        print(f"[ERROR] PyInstaller exited with code {res.returncode}")
        return False

    return True


def verify_output():
    """Check that the executable was created successfully."""
    print("[4/4] Verifying output...")
    exe_name = "EMS_Reporter.exe" if sys.platform == "win32" else "EMS_Reporter"
    target = DIST_DIR / exe_name

    if not target.exists():
        print(f"[ERROR] Target executable was not found: {target}")
        return False

    size_mb = target.stat().st_size / (1024 * 1024)
    print("\n" + "=" * 60)
    print(" [SUCCESS] Build finished successfully!")
    print(f" Executable path: {target}")
    print(f" Executable size: {size_mb:.1f} MB")
    print("=" * 60 + "\n")

    # If on Windows, open dist folder in explorer
    if sys.platform == "win32":
        try:
            os.startfile(str(DIST_DIR))
        except Exception:
            pass

    return True


def main():
    print("=" * 60)
    print("         EMS REPORTER STANDALONE COMPILER")
    print("=" * 60 + "\n")

    if not check_and_install_dependencies():
        input("\nPress Enter to exit...")
        sys.exit(1)

    clean_previous_builds()

    if not run_pyinstaller():
        input("\nPress Enter to exit...")
        sys.exit(1)

    if not verify_output():
        input("\nPress Enter to exit...")
        sys.exit(1)

    input("Press Enter to finish...")


if __name__ == "__main__":
    main()
