#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fcntl
import json
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
import sys

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from server_store.db import init_db
from server_store.renewal_repository import BEIJING_TZ, scan_due_profiles
from server_store.repository import open_repo
from server_store.runtime import load_env_file


SCAN_LOCK_PATH = Path("/tmp/seat-renewal-scan.lock")


def catch_up_day(now=None):
    current = now or datetime.now(BEIJING_TZ)
    return current.date() if current.hour >= 23 else current.date() - timedelta(days=1)


def run_scan(db_path=None, day_key: str | None = None) -> dict:
    load_env_file()
    init_db(db_path)
    conn = open_repo(db_path)
    try:
        result = scan_due_profiles(conn, day_key=day_key)
        conn.commit()
        return result
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Scan local renewal profiles and update used days")
    parser.add_argument("--db-path", default=None)
    parser.add_argument("--day", default=None, help="指定扫描日期，格式 YYYY-MM-DD")
    parser.add_argument(
        "--catch-up",
        action="store_true",
        help="自愈模式：23:00 前补到昨天，23:00 后补到今天",
    )
    args = parser.parse_args()
    day_key = args.day
    if args.catch_up and not day_key:
        day_key = catch_up_day().isoformat()
    SCAN_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with SCAN_LOCK_PATH.open("w") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        print(json.dumps(run_scan(db_path=args.db_path, day_key=day_key), ensure_ascii=False))


if __name__ == "__main__":
    main()
