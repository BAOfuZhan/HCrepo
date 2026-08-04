import assert from "node:assert/strict";
import {
  pauseUntilFromDays,
  resumeExpiredPausedUsers,
} from "../workers/tongyi/src/worker.js";

const now = Date.parse("2026-07-24T01:02:03.000Z");
assert.equal(
  pauseUntilFromDays(3, now),
  "2026-07-27T01:02:03.000Z",
);
assert.equal(pauseUntilFromDays(0, now), "");
assert.equal(pauseUntilFromDays(1.5, now), "");
assert.equal(pauseUntilFromDays(366, now), "");

const resumeAt = "2026-07-23T01:02:03.000Z";
const store = new Map([
  ["meta:paused_users", JSON.stringify([{ schoolId: "001", userId: "u1", resumeAt }])],
  ["school:001:user:u1", JSON.stringify({ id: "u1", status: "paused", pause_until: resumeAt, pause_days: 3 })],
  ["school:001:users:full", JSON.stringify([{ id: "u1", status: "paused", pause_until: resumeAt, pause_days: 3 }])],
]);
const KV = {
  get: async key => store.get(key) ?? null,
  put: async (key, value) => store.set(key, value),
};
const originalFetch = globalThis.fetch;
globalThis.fetch = async () => new Response('{"ok":true}', {
  headers: { "Content-Type": "application/json" },
});
try {
  await resumeExpiredPausedUsers({
    SEAT_KV: KV,
    SERVER_DISPATCH_API_KEY: "test-token",
    RENEWAL_API_URL: "https://example.test/api/internal/renewals",
  });
} finally {
  globalThis.fetch = originalFetch;
}
const resumed = JSON.parse(store.get("school:001:user:u1"));
assert.equal(resumed.status, "active");
assert.equal("pause_until" in resumed, false);
assert.equal("pause_days" in resumed, false);
assert.deepEqual(JSON.parse(store.get("meta:paused_users")), []);
