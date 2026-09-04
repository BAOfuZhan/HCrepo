from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import sys

sys.path.insert(0, str(Path(__file__).parents[1]))

from sign.current_reservations import collect_all, init_output_db, save_legacy_account_handoff, sync_source_references
from sign.scheduled_collect import schedule_sign_requests
from sign.execute_sign_requests import execute_due_requests


with TemporaryDirectory() as temp_dir:
    db_path = Path(temp_dir) / "sign.sqlite3"
    conn = init_output_db(db_path)
    item = {
        "school": {"id": "021", "name": "School", "apiFamily": "seat"},
        "user": {"id": "u1", "phone": "new-phone", "status": "active"},
    }
    sync_source_references(conn, [item], "2026-09-01T21:00:00+08:00", "sign-1")
    payload = {
        "signServerId": "sign-1",
        "schoolId": "021",
        "userId": "u1",
        "oldPhone": "old-phone",
        "oldPasswordCipher": "old-cipher",
        "collectFromDate": "2026-09-02",
        "reserveDate": "2026-09-02",
        "createdAt": "2026-09-01T21:00:00+08:00",
        "expiresAt": "2026-09-02T23:59:59+08:00",
    }
    handoff_id = save_legacy_account_handoff(conn, payload)
    save_legacy_account_handoff(
        conn, {**payload, "oldPhone": "middle-phone", "oldPasswordCipher": "middle-cipher"}
    )
    saved = conn.execute(
        "SELECT old_phone, old_password_cipher FROM legacy_account_handoffs WHERE id = ?",
        (handoff_id,),
    ).fetchone()
    assert (saved["old_phone"], saved["old_password_cipher"]) == ("old-phone", "old-cipher")

    conn.execute(
        "INSERT INTO user_collection_settings (user_id, sign_server_id, school_id, auto_enabled) VALUES ('u1', 'sign-1', '021', 1)"
    )
    conn.execute(
        "INSERT INTO user_sign_feature_settings (user_id, sign_server_id, school_id, visible_override) VALUES ('u1', 'sign-1', '021', 'show')"
    )
    base = (
        "sign-1", "run", "2026-09-02T04:00:00+08:00", "source", "021", "u1",
        "fid", "room", 0, "2026-09-02", "", "08:00", "room", "358", "seat",
    )
    conn.execute(
        """
        INSERT INTO current_reservation_collections (
            sign_server_id, run_id, collected_at, source_server, school_id, user_id,
            fid_enc, seat_page_id, reserve_index, today_date, start_time_raw,
            start_time_beijing, room_id, seat_id, api_family, reserve_json,
            credential_type, handoff_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'current', NULL)
        """,
        (*base, '{"id":"current-reserve","today":"2026-09-02"}'),
    )
    conn.execute(
        """
        INSERT INTO current_reservation_collections (
            sign_server_id, run_id, collected_at, source_server, school_id, user_id,
            fid_enc, seat_page_id, reserve_index, today_date, start_time_raw,
            start_time_beijing, room_id, seat_id, api_family, reserve_json,
            credential_type, handoff_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'legacy', ?)
        """,
        (*base, '{"id":"legacy-reserve","today":"2026-09-02"}', handoff_id),
    )
    conn.commit()
    conn.close()

    with patch("sign.scheduled_collect.sign_enabled_here", return_value=True):
        tasks = schedule_sign_requests(db_path, "2026-09-02", "sign-1")
    assert {(task["credentialType"], task["reserveId"]) for task in tasks} == {
        ("current", "current-reserve"),
        ("legacy", "legacy-reserve"),
    }

print("legacy sign handoff test passed")


class FakeClient:
    def __init__(self):
        self.requests = type("Requests", (), {"headers": {}})()

    def bootstrap_login(self, username, password):
        assert (username, password) == ("old-phone", "old-cipher")
        return True


with TemporaryDirectory() as temp_dir:
    db_path = Path(temp_dir) / "sign.sqlite3"
    source_item = {
        "school": {"id": "021", "name": "School", "apiFamily": "seat"},
        "user": {"id": "u1", "phone": "new-phone", "password": "new-cipher", "status": "active"},
        "targets": [{"fid_enc": "fid", "seat_page_id": "room"}],
    }
    with (
        patch("sign.current_reservations.sign_enabled_here", return_value=True),
        patch("sign.current_reservations.belongs_to_sign_server", return_value=True),
        patch("sign.current_reservations.load_source_users", return_value=[source_item]),
        patch("sign.current_reservations.reserve", return_value=FakeClient()),
        patch("sign.current_reservations.decrypt_password", side_effect=lambda value: value),
        patch("sign.current_reservations.fetch_current_reservations", return_value=("seat", [], {})),
    ):
        collect_all(
            Path(temp_dir) / "source.sqlite3", db_path, "configured", True, "sign-1", "sign-1",
            "021", "u1", credential_override={
                "old_phone": "old-phone", "old_password_cipher": "old-cipher"
            },
        )
    conn = init_output_db(db_path)
    assert conn.execute("SELECT phone FROM source_users WHERE user_id = 'u1'").fetchone()["phone"] == "new-phone"
    conn.close()

print("legacy credential isolation test passed")


class FakeResponse:
    status_code = 200
    text = "ok"

    def json(self):
        return {"success": True}

    def raise_for_status(self):
        return None


class FakeSignClient(FakeClient):
    def __init__(self):
        super().__init__()
        self.requests.get = lambda *args, **kwargs: FakeResponse()
        self.request_timeout = 5


with TemporaryDirectory() as temp_dir:
    db_path = Path(temp_dir) / "sign.sqlite3"
    conn = init_output_db(db_path)
    source_item = {
        "school": {"id": "021", "name": "School", "apiFamily": "seat"},
        "user": {"id": "u1", "phone": "new-phone", "password": "new-cipher", "status": "active"},
        "targets": [],
    }
    sync_source_references(conn, [source_item], "2026-09-01T21:00:00+08:00", "sign-1")
    handoff_id = save_legacy_account_handoff(conn, {
        "signServerId": "sign-1", "schoolId": "021", "userId": "u1",
        "oldPhone": "old-phone", "oldPasswordCipher": "old-cipher",
        "collectFromDate": "2000-01-01", "reserveDate": "2000-01-01", "createdAt": "2026-09-01T21:00:00+08:00",
        "expiresAt": "2099-09-02T23:59:59+08:00",
    })
    conn.execute(
        """
        INSERT INTO scheduled_sign_requests (
            task_key, sign_server_id, school_id, user_id, reserve_id, api_family,
            reserve_start_at, target_window, due_at, request_url, credential_type,
            handoff_id, created_at, updated_at
        ) VALUES ('legacy-task', 'sign-1', '021', 'u1', 'reserve-1', 'seat',
                  '2026-09-02T08:00:00+08:00', '08:13-08:17',
                  '2000-01-01T00:00:00+08:00', 'https://example.test/sign',
                  'legacy', ?, '', '')
        """,
        (handoff_id,),
    )
    conn.commit()
    conn.close()
    with (
        patch("sign.execute_sign_requests.sign_enabled_here", return_value=True),
        patch("sign.execute_sign_requests.belongs_to_sign_server", return_value=True),
        patch("sign.execute_sign_requests.load_source_users", return_value=[source_item]),
        patch("sign.execute_sign_requests.reserve", return_value=FakeSignClient()),
        patch("sign.execute_sign_requests.decrypt_password", side_effect=lambda value: value),
        patch("sign.execute_sign_requests.time.sleep"),
    ):
        result = execute_due_requests(Path(temp_dir) / "source.sqlite3", db_path, "sign-1")
    assert result[0]["status"] == "completed"
    conn = init_output_db(db_path)
    handoff = conn.execute(
        "SELECT sign_status, old_phone, old_password_cipher FROM legacy_account_handoffs WHERE id = ?",
        (handoff_id,),
    ).fetchone()
    assert (handoff["sign_status"], handoff["old_phone"], handoff["old_password_cipher"]) == (
        "completed", "", ""
    )
    conn.close()

print("legacy sign credential binding test passed")

scheduled_source = (Path(__file__).parents[1] / "sign/scheduled_collect.py").read_text()
assert "collect_from_date <= ? AND reserve_date >= ?" in scheduled_source
assert "today in collected_dates" in scheduled_source
assert 'final_day = today == text(handoff["reserve_date"])' in scheduled_source
print("multi-day legacy collection test passed")
