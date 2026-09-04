from pathlib import Path


source = (Path(__file__).resolve().parents[1] / "qianduan/server_api_example.py").read_text()

internal = source.split('@app.route("/api/internal/user-schedule"', 1)[1].split(
    '@app.route("/api/me/service-schedule"', 1
)[0]
assert "_require_server_dispatch_api_key()" in internal
assert "weekly_schedule_to_mapping" in internal
assert "maxSlotHours" in internal
assert "sync_now=True" in internal

relay = source.split('@app.route("/api/me/service-schedule"', 1)[1].split(
    '@app.get("/<path:asset_path>")', 1
)[0]
assert '"/api/internal/user-schedule"' in relay
assert "current_identity()" in relay
assert "_call_self_service(" in relay

policy = source.split('@app.get("/api/me/service-policy")', 1)[1].split(
    '@app.get("/<path:asset_path>")', 1
)[0]
assert "get_school_local(school_id)" in policy
assert "endSecond" in policy

update = source.split("def update_user_schedule(", 1)[1].split(
    '@app.put("/api/me/schedule")', 1
)[0]
assert "_schedule_duration_error" in update
assert "changed_schedule_slot_keys" in update
assert "push_user_to_kv_now" not in update
assert '"/api/internal/user-sync"' in update
assert 'user["sync_status"] = "pending"' in update
assert "if sync_now:" in update

print("schedule service relay check passed")
