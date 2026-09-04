from pathlib import Path


source = (Path(__file__).resolve().parents[1] / "qianduan/server_api_example.py").read_text()
update = source.split("def update_user_config(", 1)[1].split('@app.put("/api/me/user-config")', 1)[0]
assert 'user["user_top_config_enabled"] = True' in update
assert "target=push_user_to_kv_now" in update
assert 'name=f"user-config-sync-{school_id}-{user_id}"' in update

builder = source.split("def _build_user_config_payload(", 1)[1].split("def _env_flag_enabled", 1)[0]
assert 'config = config if enabled and isinstance(config, dict) else {}' in builder

receive = source.split("def internal_user_sync():", 1)[1].split('@app.post("/api/internal/user-delete")', 1)[0]
assert 'user = {**user, "user_top_config_enabled": False, "user_top_config": {}}' in receive

print("user config bidirectional sync check passed")
