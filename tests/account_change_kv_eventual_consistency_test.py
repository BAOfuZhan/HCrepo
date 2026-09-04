from pathlib import Path


source = (Path(__file__).resolve().parents[1] / "qianduan/server_api_example.py").read_text()
push = source.split("def push_user_to_kv_now(", 1)[1].split("def get_school(", 1)[0]
assert '"kvVerified": False' in push
assert '"syncPending": True' in push
assert 'status="pending"' in push
assert "raise RuntimeError(verify_error)" not in push

print("account change KV eventual consistency check passed")
