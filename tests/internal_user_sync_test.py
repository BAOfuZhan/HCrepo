import os
import sys
import tempfile
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

server_source = (Path(__file__).parents[1] / "qianduan/server_api_example.py").read_text(encoding="utf-8")
assert 'source_user["auto_sign_enabled"] = enabled' in server_source
assert 'source_user["sign_feature_visible"] = feature_visible' in server_source
assert "def _delete_sign_user_everywhere" in server_source
assert "def _delete_remote_user_or_raise" in server_source
admin_delete = server_source.split('@app.delete("/api/admin/user")', 1)[1].split('@app.get("/api/me/sign-control")', 1)[0]
assert admin_delete.index("delete_user_from_kv") < admin_delete.index("_delete_remote_user_or_raise") < admin_delete.index("repo_delete_user")
renewal_delete = server_source.split('@app.delete("/api/admin/renewal-user")', 1)[1].split('@app.post("/api/admin/renewal-channel")', 1)[0]
assert renewal_delete.index("delete_user_from_kv") < renewal_delete.index("_delete_remote_user_or_raise") < renewal_delete.index("repo_delete_user")


with tempfile.TemporaryDirectory() as temp_dir:
    os.environ.update({
        "CF_ACCOUNT_ID": "test",
        "CF_KV_NAMESPACE_ID": "test",
        "CF_API_TOKEN": "test",
        "SERVER_DISPATCH_API_KEY": "test-token",
        "SEAT_STORE_DB_PATH": os.path.join(temp_dir, "seat.sqlite3"),
        "SIGN_SOURCE_DB": os.path.join(temp_dir, "seat.sqlite3"),
        "SIGN_OUTPUT_DB": os.path.join(temp_dir, "sign.sqlite3"),
        "SIGN_CONTROL_BASE_URL": "",
        "SIGN_SERVER_ID": "sign-test",
        "SIGN_ENABLED_SERVER_ID": "sign-test",
    })

    from qianduan.server_api_example import app
    from server_store.repository import (
        get_user,
        open_repo,
        replace_school,
        replace_user,
    )

    conn = open_repo()
    replace_school(conn, {"id": "001", "name": "旧学校"})
    replace_school(conn, {"id": "002", "name": "新学校"})
    replace_user(conn, "001", {
        "id": "u1",
        "schoolId": "001",
        "phone": "13800000000",
        "status": "active",
    })
    conn.commit()
    conn.close()

    client = app.test_client()
    headers = {"X-Tongyi-Key": "test-token"}
    response = client.post("/api/internal/user-sync", headers=headers, json={
        "schoolId": "002",
        "sourceSchoolId": "001",
        "user": {
            "id": "u1",
            "schoolId": "002",
            "phone": "13900000000",
            "status": "paused",
        },
    })
    assert response.status_code == 200, response.get_data(as_text=True)

    conn = open_repo()
    assert get_user(conn, "001", "u1") is None
    assert get_user(conn, "002", "u1")["status"] == "paused"
    conn.execute(
        """
        INSERT INTO reserve_results (task_id, school_id, user_id, account, account_masked)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("task-u1", "002", "u1", "13900000000", "139****0000"),
    )
    conn.execute(
        """
        INSERT INTO reserve_results (task_id, school_id, user_id, account, account_masked)
        VALUES (?, ?, ?, ?, ?)
        """,
        ("task-legacy-phone", "002", "", "13900000000", "139****0000"),
    )
    conn.commit()
    conn.close()

    response = client.post("/api/internal/user-sync", headers=headers, json={
        "schoolId": "002",
        "user": {
            "id": "u1",
            "schoolId": "002",
            "phone": "13712345678",
            "status": "paused",
        },
    })
    assert response.status_code == 200, response.get_data(as_text=True)

    conn = open_repo()
    results = conn.execute(
        "SELECT task_id, account, account_masked FROM reserve_results "
        "WHERE task_id IN (?, ?) ORDER BY task_id",
        ("task-u1", "task-legacy-phone"),
    ).fetchall()
    assert [dict(result) for result in results] == [
        {"task_id": "task-legacy-phone", "account": "13712345678", "account_masked": "137****5678"},
        {"task_id": "task-u1", "account": "13712345678", "account_masked": "137****5678"},
    ]
    sync_job = conn.execute(
        "SELECT job_type, target_key, status FROM sync_jobs ORDER BY id DESC LIMIT 1"
    ).fetchone()
    assert dict(sync_job) == {
        "job_type": "receive_user_immediate",
        "target_key": "school:002:user:u1",
        "status": "done",
    }
    conn.close()

    from sign.current_reservations import init_output_db, sync_source_references

    response = client.post("/api/internal/user-sync", headers=headers, json={
        "schoolId": "002",
        "user": {
            "id": "u1",
            "schoolId": "002",
            "phone": "13712345678",
            "status": "paused",
        },
        "legacySignHandoff": {
            "signServerId": "",
            "schoolId": "002",
            "userId": "u1",
            "oldPhone": "13800000000",
            "oldPasswordCipher": "old-cipher",
            "collectFromDate": "2026-09-02",
            "reserveDate": "2026-09-02",
            "createdAt": "2026-09-01T19:11:00+08:00",
            "expiresAt": "2026-09-02T23:59:59+08:00",
        },
    })
    assert response.status_code == 200, response.get_data(as_text=True)
    sign_conn = init_output_db(Path(os.environ["SIGN_OUTPUT_DB"]))
    saved_handoff = sign_conn.execute(
        "SELECT sign_server_id, old_phone FROM legacy_account_handoffs WHERE user_id = ?",
        ("u1",),
    ).fetchone()
    assert dict(saved_handoff) == {
        "sign_server_id": "sign-test",
        "old_phone": "13800000000",
    }
    sign_conn.close()

    sign_conn = init_output_db(Path(os.environ["SIGN_OUTPUT_DB"]))
    sync_source_references(sign_conn, [{
        "school": {"id": "002"},
        "user": {"id": "u1", "phone": "13712345678"},
    }], "2026-08-27T10:00:00+08:00", "test-server")
    sign_conn.execute(
        "INSERT INTO user_collection_settings (user_id, sign_server_id, school_id, auto_enabled, updated_at) VALUES ('u1', 'test-server', '002', 1, '')"
    )
    sign_conn.commit()
    sign_conn.close()

    response = client.put("/api/internal/sign-control", headers={
        "X-Sign-Control-Token": "test-token",
    }, json={"schoolId": "002", "userId": "u1"})
    assert response.status_code == 400, response.get_data(as_text=True)
    sign_conn = init_output_db(Path(os.environ["SIGN_OUTPUT_DB"]))
    assert sign_conn.execute(
        "SELECT auto_enabled FROM user_collection_settings WHERE user_id = 'u1'"
    ).fetchone()["auto_enabled"] == 1
    sign_conn.close()

    response = client.post("/api/internal/user-delete", headers=headers, json={
        "schoolId": "002",
        "userId": "u1",
    })
    assert response.status_code == 200, response.get_data(as_text=True)

    conn = open_repo()
    assert get_user(conn, "002", "u1") is None
    conn.close()
    sign_conn = init_output_db(Path(os.environ["SIGN_OUTPUT_DB"]))
    assert sign_conn.execute(
        "SELECT 1 FROM user_collection_settings WHERE user_id = 'u1'"
    ).fetchone() is None
    assert sign_conn.execute(
        "SELECT user_status FROM source_users WHERE user_id = 'u1'"
    ).fetchone()["user_status"] == "deleted"
    sign_conn.close()
