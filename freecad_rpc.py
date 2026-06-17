#!/usr/bin/env python3
"""Small XML-RPC client for the live FreeCAD GUI macro.

The matching FreeCAD macro is:
  ~/.local/share/FreeCAD/Macro/van_rpc_server.FCMacro

It exposes ping(), execute_code(code), and save_screenshot(path, w, h, view)
on 127.0.0.1:9875.
"""

import argparse
import pathlib
import sys
import xmlrpc.client


URL = "http://127.0.0.1:9875"


def client():
    return xmlrpc.client.ServerProxy(URL, allow_none=True)


def main(argv=None):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("ping")

    exec_parser = sub.add_parser("exec")
    exec_parser.add_argument("code")

    exec_file = sub.add_parser("exec-file")
    exec_file.add_argument("path")

    shot = sub.add_parser("screenshot")
    shot.add_argument("path")
    shot.add_argument("--width", type=int, default=1400)
    shot.add_argument("--height", type=int, default=900)
    shot.add_argument("--view", default="Isometric")

    args = parser.parse_args(argv)
    rpc = client()

    if args.command == "ping":
        print(rpc.ping())
        return 0

    if args.command == "exec":
        result = rpc.execute_code(args.code)
    elif args.command == "exec-file":
        code = pathlib.Path(args.path).read_text(encoding="utf-8")
        result = rpc.execute_code(code)
    elif args.command == "screenshot":
        result = rpc.save_screenshot(args.path, args.width, args.height, args.view)
    else:
        parser.error("unknown command")

    if not result.get("success"):
        print(result.get("error", ""), file=sys.stderr)
        return 1
    print(result.get("output") or result.get("path") or "")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
