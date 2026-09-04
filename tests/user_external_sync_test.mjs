import assert from "node:assert/strict";
import {
  syncSignSettings,
  syncUserDeleteToServer,
  syncUserToServer,
} from "../workers/tongyi/src/worker.js";

const requests = [];
globalThis.fetch = async (url, options) => {
  requests.push({ url: String(url), options });
  return new Response('{"ok":true}', {
    headers: { "Content-Type": "application/json" },
  });
};
const env = {
  RENEWAL_API_URL: "https://example.test/api/internal/renewals",
  SERVER_DISPATCH_API_KEY: "test-token",
};

await syncUserToServer(env, "002", { id: "u1" }, "001");
await syncUserDeleteToServer(env, "002", "u1");

assert.equal(requests[0].url, "https://example.test/api/internal/user-sync");
assert.deepEqual(JSON.parse(requests[0].options.body), {
  schoolId: "002",
  user: { id: "u1" },
  sourceSchoolId: "001",
});
assert.equal(requests[1].url, "https://example.test/api/internal/user-delete");
assert.deepEqual(JSON.parse(requests[1].options.body), {
  schoolId: "002",
  userId: "u1",
});

requests.length = 0;
await syncSignSettings(env, "002", { id: "u1" });
assert.equal(requests.length, 0);

await syncSignSettings(env, "002", {
  id: "u1",
  sign_feature_visible: false,
  auto_sign_enabled: false,
});
assert.equal(requests.length, 2);
assert.deepEqual(JSON.parse(requests[0].options.body), {
  schoolId: "002",
  userId: "u1",
  override: "hide",
});
assert.deepEqual(JSON.parse(requests[1].options.body), {
  schoolId: "002",
  userId: "u1",
  enabled: false,
});

requests.length = 0;
await syncSignSettings(env, "002", { id: "u1", sign_feature_visible: true });
assert.equal(requests.length, 1);
assert.equal(new URL(requests[0].url).pathname, "/api/internal/sign-feature-user");

requests.length = 0;
await syncSignSettings(env, "002", { id: "u1", auto_sign_enabled: false });
assert.equal(requests.length, 1);
assert.equal(new URL(requests[0].url).pathname, "/api/internal/sign-control");
assert.equal(JSON.parse(requests[0].options.body).enabled, false);

requests.length = 0;
await syncSignSettings(env, "002", { id: "u1", auto_sign_enabled: true });
assert.equal(requests.length, 1);
assert.equal(new URL(requests[0].url).pathname, "/api/internal/sign-control");
assert.equal(JSON.parse(requests[0].options.body).enabled, true);
