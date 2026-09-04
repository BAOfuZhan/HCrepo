from pathlib import Path


source = (Path(__file__).resolve().parents[1] / "qianduan/server_api_example.py").read_text()
helper = source.split("def effective_paused_streak_days", 1)[1].split("def user_renewal_expired", 1)[0]
expired = source.split("def user_renewal_expired", 1)[1].split("def user_auth_fingerprint", 1)[0]
start = source.split("def user_self_start_blocked", 1)[1].split("def settle_user_pause_after_resume", 1)[0]

assert '== "paused"' in helper
assert "> overdue_days + 4" in helper
assert "last_paused_at" in helper
assert "not renewal_expiry_covered_by_pause" in expired
assert "not renewal_expiry_covered_by_pause" in start
print("paused expired login rule check passed")
