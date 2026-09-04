import assert from "node:assert/strict";
import { syncSignSettings } from "../workers/tongyi/src/worker.js";

const users = new Map();
for (let i = 0; i < 1000; i += 1) {
  users.set(`u${i}`, { visible: i % 2 === 0, enabled: i % 2 === 0 });
}

const requests = [];
globalThis.fetch = async (url, options) => {
  const path = new URL(url).pathname;
  const body = JSON.parse(options.body);
  const state = users.get(body.userId);
  requests.push({ path, body });
  await Promise.resolve();
  if (path.endsWith("/sign-feature-user")) {
    state.visible = body.override === "show";
    if (!state.visible) state.enabled = false;
  } else if (path.endsWith("/sign-control")) {
    state.enabled = body.enabled;
  }
  return new Response('{"ok":true}', { headers: { "Content-Type": "application/json" } });
};

const env = {
  RENEWAL_API_URL: "https://example.test/api/internal/renewals",
  SERVER_DISPATCH_API_KEY: "test-token",
};

// Missing fields simulate pause/resume and legacy school migration payloads.
await Promise.all(Array.from({ length: 500 }, (_, i) =>
  syncSignSettings(env, "target-school", { id: `u${i}` })
));
assert.equal(requests.length, 0);
for (let i = 0; i < 500; i += 1) {
  assert.equal(users.get(`u${i}`).enabled, i % 2 === 0);
}

// Explicit values simulate user/admin operations, with many simultaneous users.
await Promise.all(Array.from({ length: 1000 }, (_, i) =>
  syncSignSettings(env, "target-school", {
    id: `u${i}`,
    sign_feature_visible: true,
    auto_sign_enabled: i % 3 === 0,
  })
));
assert.equal(requests.length, 2000);
for (let i = 0; i < 1000; i += 1) {
  assert.equal(users.get(`u${i}`).visible, true);
  assert.equal(users.get(`u${i}`).enabled, i % 3 === 0);
}

// Duplicate retries are idempotent and a partial explicit true must stay true.
requests.length = 0;
await Promise.all(Array.from({ length: 100 }, () =>
  syncSignSettings(env, "target-school", { id: "u1", auto_sign_enabled: true })
));
assert.equal(requests.length, 100);
assert.equal(users.get("u1").enabled, true);

console.log("sign state load simulation passed");
