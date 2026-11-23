"""Waraq Library Studio — application entry point."""
from __future__ import annotations

import argparse
import json

from waraq.config import HOST, PORT
from waraq.security import reset_demo_accounts
from waraq.storage import database_health, init_db
from waraq.web import run_server


def main() -> None:
    parser = argparse.ArgumentParser(description="Waraq Library Studio")
    parser.add_argument("--host", default=HOST, help="Bind address (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=PORT, help="Port (default: 8000)")
    parser.add_argument("--reset-demo-accounts", action="store_true",
                        help="Restore local demo logins without deleting library records.")
    parser.add_argument("--check", action="store_true", help="Initialize and check the local database, then exit.")
    args = parser.parse_args()

    if args.reset_demo_accounts:
        reset_demo_accounts()
        print("Demo accounts restored (catalogue and loan records were preserved).")
        print("Manager: admin / admin123")
        print("Member:  saif_101 / saif123")
        print("Member:  rida_102 / rida123")
        print("Member:  aws_103 / aws123")
        return

    if args.check:
        init_db()
        result = database_health()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        raise SystemExit(0 if result["ok"] else 1)

    run_server(args.host, args.port)


if __name__ == "__main__":
    main()
