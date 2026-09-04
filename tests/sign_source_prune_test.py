from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).parents[1]))

from sign.current_reservations import init_output_db, sync_source_references


source = (Path(__file__).parents[1] / "sign/current_reservations.py").read_text(encoding="utf-8")

assert "prune_missing: bool = False" in source
assert "if prune_missing and items:" in source
assert "user_status = 'deleted'" in source
assert "cancelled: user removed from source database" in source
assert "DELETE FROM source_users" not in source
assert "DELETE FROM collection_attempts WHERE collected_at < ?" in source
assert "DELETE FROM collection_attempts WHERE sign_server_id" not in source
assert "user_id NOT IN" in source

with tempfile.TemporaryDirectory() as temp_dir:
    conn = init_output_db(Path(temp_dir) / "sign.sqlite3")
    sync_source_references(conn, [
        {"school": {"id": "001"}, "user": {"id": "u1", "phone": "13800000000"}},
        {"school": {"id": "002"}, "user": {"id": "u2", "phone": "13900000000"}},
    ], "2026-08-20T10:00:00+08:00", "server-1", prune_missing=True)
    rows = conn.execute("SELECT user_id, phone FROM source_users ORDER BY user_id").fetchall()
    assert [(row["user_id"], row["phone"]) for row in rows] == [
        ("u1", "13800000000"),
        ("u2", "13900000000"),
    ]
    sync_source_references(conn, [{
        "school": {"id": "003"},
        "user": {"id": "u3", "phone": "13700000000", "auto_sign_enabled": True},
    }], "2026-08-20T10:00:30+08:00", "server-1")
    assert conn.execute(
        "SELECT auto_enabled FROM user_collection_settings WHERE user_id = 'u3'"
    ).fetchone()["auto_enabled"] == 1
    assert conn.execute(
        "SELECT visible_override FROM user_sign_feature_settings WHERE user_id = 'u3'"
    ).fetchone()["visible_override"] == "show"
    conn.execute("UPDATE user_collection_settings SET auto_enabled = 0 WHERE user_id = 'u3'")
    conn.execute("UPDATE user_sign_feature_settings SET visible_override = 'hide' WHERE user_id = 'u3'")
    sync_source_references(conn, [{
        "school": {"id": "003"},
        "user": {"id": "u3", "phone": "13700000000", "auto_sign_enabled": True},
    }], "2026-08-20T10:00:40+08:00", "server-1")
    assert conn.execute(
        "SELECT auto_enabled FROM user_collection_settings WHERE user_id = 'u3'"
    ).fetchone()["auto_enabled"] == 0
    assert conn.execute(
        "SELECT visible_override FROM user_sign_feature_settings WHERE user_id = 'u3'"
    ).fetchone()["visible_override"] == "hide"
    conn.execute(
        "INSERT INTO user_collection_settings (user_id, sign_server_id, school_id, auto_enabled, updated_at) VALUES (?, ?, ?, 1, ?)",
        ("u2", "server-1", "002", "2026-08-20T10:01:00+08:00"),
    )
    sync_source_references(conn, [
        {"school": {"id": "001"}, "user": {"id": "u1", "phone": "13800000000"}},
    ], "2026-08-21T10:00:00+08:00", "server-1", prune_missing=True)
    assert conn.execute(
        "SELECT auto_enabled FROM user_collection_settings WHERE user_id = 'u2'"
    ).fetchone()["auto_enabled"] == 1
    sync_source_references(conn, [
        {"school": {"id": "001"}, "user": {"id": "u1", "phone": "13800000000"}},
        {"school": {"id": "002"}, "user": {"id": "u2", "phone": "13900000000", "status": "paused"}},
    ], "2026-08-21T12:00:00+08:00", "server-1", prune_missing=True)
    assert conn.execute(
        "SELECT auto_enabled FROM user_collection_settings WHERE user_id = 'u2'"
    ).fetchone()["auto_enabled"] == 1
    sync_source_references(conn, [
        {"school": {"id": "001"}, "user": {"id": "u1", "phone": "13800000000"}},
        {"school": {"id": "002"}, "user": {"id": "u2", "phone": "13900000000", "status": "active"}},
    ], "2026-08-22T10:00:00+08:00", "server-1", prune_missing=True)
    assert conn.execute(
        "SELECT auto_enabled FROM user_collection_settings WHERE user_id = 'u2'"
    ).fetchone()["auto_enabled"] == 1
    conn.close()

print("sign source pruning guard passed")
