import assert from "node:assert/strict";
import {
  buildChaoxingSeatPageUrl,
  didLoginAccountChange,
  extractPageToken,
  validateChaoxingSeatPage,
} from "../workers/tongyi/src/worker.js";

assert.equal(didLoginAccountChange("13800000000", "13800000000"), false);
assert.equal(didLoginAccountChange("13800000000", "13900000000"), true);

assert.equal(
  extractPageToken('<input type="hidden" id="pageToken" value="page-token">'),
  "page-token",
);
assert.equal(
  extractPageToken('<input value="token-first" name="token" type="hidden">'),
  "token-first",
);

const url = new URL(buildChaoxingSeatPageUrl(
  { fidEnc: "unit-1" },
  {
    schedule: {
      Monday: {
        slots: [
          { roomid: "wrong-room", fidEnc: "wrong-unit" },
          { roomid: "12", seatid: "56", seatPageId: "34" },
        ],
      },
    },
  },
  "seat",
));
assert.equal(url.pathname, "/front/third/apps/seat/select");
assert.equal(url.searchParams.get("id"), "12");
assert.equal(url.searchParams.get("seatId"), "34");
assert.equal(url.searchParams.get("fidEnc"), "unit-1");
assert.equal(url.searchParams.get("backLevel"), "2");
assert.match(url.searchParams.get("day"), /^\d{4}-\d{2}-\d{2}$/);

let requests = 0;
const requestedUrls = [];
const originalFetch = globalThis.fetch;
globalThis.fetch = async (requestUrl) => {
  requests += 1;
  requestedUrls.push(new URL(requestUrl));
  return new Response("<html>no page token</html>");
};
try {
  const result = await validateChaoxingSeatPage(
    new Map(),
    { schedule: { Monday: { slots: [{ roomid: "12", seatid: "56", seatPageId: "34", fidEnc: "user-unit" }] } } },
    { seat_api_mode: "seat", fidEnc: "school-unit" },
  );
  assert.equal(result.ok, false);
  assert.equal(result.attempts, 3);
  assert.equal(requests, 3);
  assert.ok(requestedUrls.every(item => item.pathname === "/front/third/apps/seat/select"));
  assert.ok(requestedUrls.every(item => item.searchParams.get("id") === "12"));
  assert.ok(requestedUrls.every(item => item.searchParams.get("seatId") === "34"));
  assert.ok(requestedUrls.every(item => item.searchParams.get("fidEnc") === "user-unit"));
} finally {
  globalThis.fetch = originalFetch;
}
