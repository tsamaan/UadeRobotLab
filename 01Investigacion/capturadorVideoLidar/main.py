#!/usr/bin/env python3
"""Entry point for the Unitree video/LiDAR capture tool."""

import sys


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args or args[0] == "--gui":
        from robot_capture.gui import main as gui_main

        raise SystemExit(gui_main(args[1:] if args else []))
    if args[0] == "--console":
        from robot_capture.cli import main as cli_main

        raise SystemExit(cli_main(args[1:]))

    from robot_capture.cli import main as cli_main

    raise SystemExit(cli_main(args))
