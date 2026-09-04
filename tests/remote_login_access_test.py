from pathlib import Path


source = (Path(__file__).resolve().parents[1] / "qianduan/server_api_example.py").read_text()
login = source.split('@app.post("/api/login")', 1)[1].split('@app.post("/api/admin/login")', 1)[0]
access = source.split('@app.post("/api/internal/user-access")', 1)[1].split("def update_user_status", 1)[0]

assert '"/api/internal/user-access"' in source
assert "if self_service_base_url:" in login
assert "_remote_user_access(resolved_school_id, matched)" in login
assert "if not access.get(\"allowed\")" in login
assert 'session["renewal_expires_on"]' in source
assert 'session["renewal_pause_covered"]' in source
assert "_require_server_dispatch_api_key()" in access
assert "allowed = not user_renewal_expired(user)" in access
assert '"expiresOn": expires_on' in access
assert '"pauseCovered": pause_covered' in access
assert 'session_expires_on = _normalize_secret(session.get("renewal_expires_on"))' in source
assert 'settled_expires_on = _normalize_secret(settle.get("expiresOn"))' in source
assert '"renewal_expires_on" not in session' in source
assert '"renewal": current_user_renewal_payload(matched)' in source
assert '"renewal": current_user_renewal_payload(user)' in source
assert "_remote_user_access(school_id, user)" in source
print("remote login access check passed")
