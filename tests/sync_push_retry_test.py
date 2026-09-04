from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import server_store.sync_push as sync_push


class FakeKV:
    def __init__(self, expected, ready_after=2):
        self.expected = expected
        self.ready_after = ready_after
        self.attempt = 0

    def get_json(self, key):
        ready = self.attempt >= self.ready_after
        if key.endswith(":users:full"):
            self.attempt += 1
            return [self.expected] if ready else []
        if key.endswith(":users"):
            return [self.expected["id"]] if ready else []
        return self.expected if ready else {"id": self.expected["id"], "status": "active"}


expected = {"id": "u1", "schoolId": "001", "status": "paused", "schedule": {}}
original_sleep = sync_push.time.sleep
sync_push.time.sleep = lambda _seconds: None
try:
    delayed = FakeKV(expected)
    assert sync_push.verify_user(delayed, "001", "u1", expected) is True
    assert delayed.attempt == 3
    assert sync_push.verify_user(FakeKV(expected, ready_after=99), "001", "u1", expected) is False
finally:
    sync_push.time.sleep = original_sleep

source = Path(sync_push.__file__).read_text()
assert 'f"school:{school_id}:users"' in source
assert 'kv.put_json("meta:paused_users", paused_users)' in source
assert "KV 三份用户数据在等待 30 秒后仍不一致" in source

runtime_source = (Path(sync_push.__file__).parent / "runtime.py").read_text()
assert 'KV_HTTP_TIMEOUT_SECONDS", "45"' in runtime_source
print("background KV retry check passed")
