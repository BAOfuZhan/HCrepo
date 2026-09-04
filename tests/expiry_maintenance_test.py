from pathlib import Path


repository = (Path(__file__).resolve().parents[1] / "server_store/renewal_repository.py").read_text()
maintenance = (Path(__file__).resolve().parents[1] / "server_store/database_maintenance.py").read_text()
enforce = repository.split("def pause_expired_active_users", 1)[1].split("def scan_due_profiles", 1)[0]

assert 'normalize_status(user.get("status"), "") != "active"' in enforce
assert "_settle_resumed_pause_streak" in enforce
assert "current_day <= expires_day" in enforce
assert "_mark_user_paused_for_expiry" in enforce
assert "pause_expired_active_users(conn)" in maintenance
assert "scan_due_profiles" not in maintenance
print("32-minute expiry enforcement check passed")
