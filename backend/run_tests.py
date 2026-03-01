#!/usr/bin/env python3
"""
Run all tests for MoneyTrack backend.

Usage:
    python run_tests.py           # Run all tests
    python run_tests.py -v        # Verbose output
    python run_tests.py -k auth   # Run only tests matching 'auth'
"""

import subprocess
import sys
import os


def main():
    # Change to the app directory where tests are located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.join(script_dir, "app")

    # Build pytest command
    cmd = [sys.executable, "-m", "pytest", app_dir]

    # Add any additional arguments passed to this script
    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])
    else:
        # Default: verbose output
        cmd.append("-v")

    # Run tests
    result = subprocess.run(cmd)

    # Exit with pytest's exit code
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
