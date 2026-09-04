import datetime
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
        "FLASK_SECRET_KEY": "test-session-secret",
        "SEAT_STORE_DB_PATH": str(Path(temp_dir) / "seat.sqlite3"),
    })

    import qianduan.server_api_example as server

    assert server.app.config["PERMANENT_SESSION_LIFETIME"] == datetime.timedelta(days=30)

    original_get_profile = server.renewal_get_profile
    server.renewal_get_profile = lambda _conn, _phone: {"expiresOn": "2026-07-23"}
    try:
        assert server.user_renewal_expired(
            {"phone": "13800000000"},
            today=datetime.date(2026, 7, 24),
        )
        assert not server.user_renewal_expired(
            {"phone": "13800000000"},
            today=datetime.date(2026, 7, 23),
        )
    finally:
        server.renewal_get_profile = original_get_profile

    assert not server.user_self_start_blocked(
        {"expiresOn": "2026-07-24", "pausedStreakDays": 6},
        {"status": "paused", "last_paused_at": "2026-07-18T10:00:00+08:00"},
        today=datetime.date(2026, 7, 31),
    )
    assert server.user_self_start_blocked(
        {"expiresOn": "2026-07-24", "pausedStreakDays": 6},
        {"status": "paused", "last_paused_at": "2026-07-27T10:00:00+08:00"},
        today=datetime.date(2026, 7, 31),
    )

    source = (Path(server.BASE_DIR) / "server_api_example.py").read_text(encoding="utf-8")
    assert 'settle_user_pause_after_resume(user) if next_status == "active" else None' in source
    assert '"/api/internal/user-sync",\n                {"schoolId": school_id, "user": user},' in source
    assert 'if _sign_runtime_status().get("enabled"):\n            _sync_sign_source_references()' in source
    renewal_source = (Path(server.BASE_DIR) / "renewal.js").read_text(encoding="utf-8")
    assert 'data-action="status"' in renewal_source
    assert 'renewalFetch("/api/admin/user-status"' in renewal_source
    assert server.settle_user_pause_after_resume({"phone": "missing-profile"}) == {
        "ok": True,
        "settled": False,
        "countedDays": 0,
        "extendedDays": 0,
        "pendingPauseDays": 0,
    }

    original_user = {"id": "u1", "phone": "13800000000", "password": "cipher-a"}
    original_fingerprint = server.user_auth_fingerprint(original_user)
    assert original_fingerprint != server.user_auth_fingerprint({**original_user, "phone": "13900000000"})
    assert original_fingerprint != server.user_auth_fingerprint({**original_user, "password": "cipher-b"})

    for asset in ("simple-login.js", "Userconfigure.js", "app.js", "admin-auth.js"):
        source = (Path(server.BASE_DIR) / asset).read_text(encoding="utf-8")
        assert "localStorage.setItem(PERSISTED_LOGIN_KEY" not in source
        assert "localStorage.setItem(ADMIN_PERSISTED_LOGIN_KEY" not in source
