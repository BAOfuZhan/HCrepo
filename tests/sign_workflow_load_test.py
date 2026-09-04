import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).parents[1]))


with TemporaryDirectory() as temp_dir:
    os.environ.update({
        "CF_ACCOUNT_ID": "test",
        "CF_KV_NAMESPACE_ID": "test",
        "CF_API_TOKEN": "test",
        "SERVER_DISPATCH_API_KEY": "test-token",
        "SIGN_CONTROL_TOKEN": "test-token",
        "SIGN_SERVER_ID": "sign-1",
        "SIGN_ENABLED_SERVER_ID": "sign-1",
        "SEAT_STORE_DB_PATH": str(Path(temp_dir) / "seat.sqlite3"),
        "SIGN_OUTPUT_DB": str(Path(temp_dir) / "sign.sqlite3"),
        "SIGN_CONTROL_BASE_URL": "",
    })

    from qianduan.server_api_example import app
    from server_store.repository import open_repo, replace_school, replace_user
    from sign.current_reservations import (
        init_output_db,
        save_legacy_account_handoff,
        sync_source_references,
    )

    user_count = 240
    conn = open_repo()
    replace_school(conn, {"id": "021", "name": "Source"})
    replace_school(conn, {"id": "022", "name": "Target"})
    for i in range(user_count):
        replace_user(conn, "021", {
            "id": f"u{i}", "schoolId": "021", "phone": f"138{i:08d}",
            "status": "active",
        })
    conn.commit()
    conn.close()

    sign_conn = init_output_db(Path(os.environ["SIGN_OUTPUT_DB"]))
    items = [{
        "school": {"id": "021", "name": "Source", "apiFamily": "seat"},
        "user": {"id": f"u{i}", "phone": f"138{i:08d}", "status": "active"},
    } for i in range(user_count)]
    sync_source_references(sign_conn, items, "2026-09-01T12:00:00+08:00", "sign-1")
    sign_conn.executemany(
        "INSERT INTO user_sign_feature_settings "
        "(user_id, sign_server_id, school_id, visible_override) VALUES (?, 'sign-1', '021', 'show')",
        [(f"u{i}",) for i in range(user_count)],
    )
    sign_conn.executemany(
        "INSERT INTO user_collection_settings "
        "(user_id, sign_server_id, school_id, auto_enabled) VALUES (?, 'sign-1', '021', ?)",
        [(f"u{i}", i % 2) for i in range(user_count)],
    )
    sign_conn.commit()
    sign_conn.close()

    headers = {"X-Sign-Control-Token": "test-token"}

    def update(index):
        with app.test_client() as client:
            body = {"schoolId": "021", "userId": f"u{index}"}
            if index >= 80:
                body["enabled"] = index >= 160
            response = client.put("/api/internal/sign-control", headers=headers, json=body)
            return index, response.status_code

    original_thread_start = threading.Thread.start

    def start_test_thread(thread):
        if thread.name.startswith("sign-choice-sync-"):
            return None
        return original_thread_start(thread)

    with (
        patch("threading.Thread.start", new=start_test_thread),
        patch("subprocess.run"),
        ThreadPoolExecutor(max_workers=24) as pool,
    ):
        statuses = dict(pool.map(update, range(user_count)))

    assert all(statuses[i] == 400 for i in range(80))
    assert all(statuses[i] == 200 for i in range(80, user_count))
    sign_conn = init_output_db(Path(os.environ["SIGN_OUTPUT_DB"]))
    states = dict(sign_conn.execute(
        "SELECT user_id, auto_enabled FROM user_collection_settings"
    ).fetchall())
    assert all(states[f"u{i}"] == i % 2 for i in range(80))
    assert all(states[f"u{i}"] == 0 for i in range(80, 160))
    assert all(states[f"u{i}"] == 1 for i in range(160, user_count))

    # Moving schools or pausing users updates references, never their saved switch.
    moved = [{
        "school": {"id": "022", "name": "Target", "apiFamily": "seat"},
        "user": {"id": f"u{i}", "phone": f"138{i:08d}", "status": "paused"},
    } for i in range(60)]
    sync_source_references(sign_conn, moved, "2026-09-01T13:00:00+08:00", "sign-1")
    moved_rows = sign_conn.execute(
        "SELECT user_id, school_id, auto_enabled FROM user_collection_settings "
        "WHERE user_id IN (%s)" % ",".join("?" * 60),
        [f"u{i}" for i in range(60)],
    ).fetchall()
    assert all(row["school_id"] == "022" for row in moved_rows)
    assert all(row["auto_enabled"] == int(row["user_id"][1:]) % 2 for row in moved_rows)

    # Repeated account changes keep only the first old credential for one cycle.
    for i in range(120):
        payload = {
            "signServerId": "sign-1", "schoolId": "021", "userId": f"u{i}",
            "oldPhone": f"old-{i}", "oldPasswordCipher": f"cipher-{i}",
            "collectFromDate": "2026-09-02", "reserveDate": "2026-09-03",
            "createdAt": "2026-09-01T21:00:00+08:00",
            "expiresAt": "2026-09-03T23:59:59+08:00",
        }
        save_legacy_account_handoff(sign_conn, payload)
        save_legacy_account_handoff(sign_conn, {
            **payload, "oldPhone": f"later-{i}", "oldPasswordCipher": f"later-cipher-{i}",
        })
    sign_conn.commit()
    handoffs = sign_conn.execute(
        "SELECT user_id, old_phone, reserve_date, collect_from_date "
        "FROM legacy_account_handoffs ORDER BY id"
    ).fetchall()
    assert len(handoffs) == 120
    assert all(row["old_phone"] == f"old-{row['user_id'][1:]}" for row in handoffs)
    assert all(row["collect_from_date"] == "2026-09-02" for row in handoffs)
    assert all(row["reserve_date"] == "2026-09-03" for row in handoffs)
    sign_conn.close()

print("full sign workflow load simulation passed")
