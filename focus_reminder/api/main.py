from __future__ import annotations

import argparse

from focus_reminder.api.server import run_api_server


def main() -> int:
    parser = argparse.ArgumentParser(description="Focus Reminder local API server")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host, default 127.0.0.1")
    parser.add_argument("--port", type=int, default=8787, help="Bind port, default 8787")
    args = parser.parse_args()

    run_api_server(host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

