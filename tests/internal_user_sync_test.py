import os
import sys
import tempfile
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


with tempfile.TemporaryDirectory() as temp_dir:
    os.environ.update({
        "CF_ACCOUNT_ID": "test",
        "CF_KV_NAMESPACE_ID": "test",
        "CF_API_TOKEN": "test",
        "SERVER_DISPATCH_API_KEY": "test-token",
        "SEAT_STORE_DB_PATH": os.path.join(temp_dir, "seat.sqlite3"),
        "SIGN_CONTROL_BASE_URL": "",
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
    replace_user(conn, "001", {"id": "u1", "schoolId": "001", "status": "active"})
    conn.commit()
    conn.close()

    client = app.test_client()
    headers = {"X-Tongyi-Key": "test-token"}
    response = client.post("/api/internal/user-sync", headers=headers, json={
        "schoolId": "002",
        "sourceSchoolId": "001",
        "user": {"id": "u1", "schoolId": "002", "status": "paused"},
    })
    assert response.status_code == 200, response.get_data(as_text=True)

    conn = open_repo()
    assert get_user(conn, "001", "u1") is None
    assert get_user(conn, "002", "u1")["status"] == "paused"
    conn.close()

    response = client.post("/api/internal/user-delete", headers=headers, json={
        "schoolId": "002",
        "userId": "u1",
    })
    assert response.status_code == 200, response.get_data(as_text=True)

    conn = open_repo()
    assert get_user(conn, "002", "u1") is None
    conn.close()
