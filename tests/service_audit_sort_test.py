from pathlib import Path


source = (Path(__file__).resolve().parents[1] / "qianduan/server_api_example.py").read_text()
route = source.split('@app.get("/api/admin/service-audits")', 1)[1].split(
    '@app.post("/api/admin/service-audits/complete-user")', 1
)[0]
assert "LEFT JOIN schools" in route
assert "COALESCE(NULLIF(s.conflict_group, ''), a.school_id)" in route
assert "a.school_id, a.phone, a.id DESC" in route
assert '"schoolName": row["school_name"]' in route
assert '"conflictGroup": row["conflict_group"]' in route
assert "LEFT JOIN users" in route
assert '"username": row["username"]' in route
assert "/api/internal/renewal-profile?" in source
assert '"purchaseChannel": renewal.get("purchaseChannel", "")' in route
assert "renewal_profile = renewal_get_profile(" in source
assert 'renewal_profile.get("purchaseChannel")' in source
assert '"currentStatus": renewal.get("currentStatus", "")' in route
assert "_audit_renewal_profiles(school_id)" in route

assert "school_lock.acquire(timeout=3.5)" in source
assert "audit_renewal_slot.acquire(timeout=3.5)" in source
assert "timeout=3" in source
assert 'now - cached["createdAt"] < 30' in source
assert 'SELECT id, action, status, detail_json, created_at' in source
assert '@app.post("/api/admin/service-audits/reply-user")' in source
assert '@app.post("/api/me/service-report/reply")' in source
assert 'append_service_message(row["detail_json"], "admin", reply)' in source
assert 'append_service_message(row["detail_json"], "user", reply)' in source
assert 'SELF_SERVICE_ENABLED_ENV = "ENABLE_SELF_SERVICE"' in source
assert "restrict_self_service_to_enabled_server" in source
assert 'path.startswith("/api/admin/service-audits")' in source
print("service audit sort check passed")
