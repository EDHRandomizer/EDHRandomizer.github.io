#!/usr/bin/env python3
"""
Quick test runner for multiplayer session tests
Usage: python run_tests.py [--headed] [--slow]
"""

import sys
import subprocess
import os

def main():
    args = [
        "pytest",
        "tests/test_multiplayer_session.py",
        "-v",  # Verbose
        "-s",  # Show print statements
    ]
    
    # Parse simple flags
    if "--headed" in sys.argv or "-h" in sys.argv:
        # Run with visible browser
        args.append("--headed")
        print("🖥️  Running tests with visible browser...")
    else:
        print("👻 Running tests in headless mode...")
    
    if "--slow" in sys.argv:
        # Slow down execution to watch what's happening
        args.append("--slowmo=500")
        print("🐌 Running with 500ms slowdown between actions...")
    
    if "--help" in sys.argv:
        print("""
EDH Randomizer Multiplayer Session Test Runner

Usage: python run_tests.py [options]

Options:
  --headed, -h    Run tests with visible browser (watch the test)
  --slow          Slow down test execution (500ms between actions)
  --help          Show this help message

Examples:
  python run_tests.py              # Run headless (fast)
  python run_tests.py --headed     # Watch the test run
  python run_tests.py --headed --slow  # Watch in slow motion

Individual tests:
  pytest tests/test_multiplayer_session.py::test_full_multiplayer_session -v -s
  pytest tests/test_multiplayer_session.py::test_late_join_during_rolling -v -s
  pytest tests/test_multiplayer_session.py::test_cannot_join_after_selecting -v -s
  pytest tests/test_multiplayer_session.py::test_url_session_restore -v -s
        """)
        return 0
    
    print("\n" + "="*60)
    print("🧪 Running EDH Randomizer Multiplayer Tests")
    print("="*60 + "\n")
    
    # Run pytest
    result = subprocess.run(args)
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
