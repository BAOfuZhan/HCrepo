from pathlib import Path


source = (Path(__file__).resolve().parents[1] / "qianduan/server_api_example.py").read_text()
assert source.count("DELETE FROM service_audits WHERE created_at < ?") == 3
assert "action <> '退款'" not in source

delete_user = source.split('def admin_delete_user():', 1)[1].split('@app.delete("/api/admin/renewal-user")', 1)[0]
assert "DELETE FROM service_audits" not in delete_user

print("refund audit retention check passed")
