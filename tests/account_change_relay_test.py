from pathlib import Path


source = (Path(__file__).resolve().parents[1] / "qianduan/server_api_example.py").read_text()

self_service = source.split('@app.put("/api/me/account")', 1)[1].split(
    '@app.put("/api/admin/user-account")', 1
)[0]
assert '"/api/internal/user-account-change"' in self_service
assert "_call_self_service(" in self_service
assert "oldPhone" in self_service
assert 'str(remote.get("error") or "修改失败，原因未知")' in self_service
assert "session.clear()" in self_service
assert "establish_user_session(school_id, refreshed_user, access)" in self_service
assert '"autoLoggedIn": True' in self_service
assert '"loggedOut": False' in self_service
assert "push_user_to_kv_now" not in self_service
assert "cache_user" not in self_service

internal = source.split('@app.put("/api/internal/user-account-change")', 1)[1].split(
    '@app.post("/api/me/status")', 1
)[0]
assert "_require_server_dispatch_api_key()" in internal
assert "find_users_by_phone_across_schools(old_phone)" in internal
assert "reserve_offset > 0" in source
assert "grab_date + timedelta(days=reserve_offset)" in source
assert '"collectFromDate": (grab_date + timedelta(days=1)).isoformat()' in source
assert "configured_enabled_sign_server_id()," in source
assert "urlparse(sign_control_base_url).hostname," in source
assert 'urlparse(f"//{sign_control_base_url}").hostname,' in source
assert "if not sign_target_server_id:" in source
assert "为避免旧账号交接失效，本次未更换账号" in source
assert '"signServerId": sign_target_server_id' in source
assert "return update_user_account(" in internal

user_sync = source.split("def internal_user_sync():", 1)[1].split(
    '@app.post("/api/internal/user-delete")', 1
)[0]
assert "or sign_configured_server_id()" in user_sync

print("account change relay check passed")
