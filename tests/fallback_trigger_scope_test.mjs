import assert from "node:assert/strict";
import {
  buildFallbackTriggerKey,
  formalTriggerScope,
} from "../workers/tongyi/src/worker.js";

assert.equal(formalTriggerScope({ trigger_time: "21:55" }), "formal-21-55");
assert.equal(formalTriggerScope({ trigger_time: "7:05" }), "formal-07-05");
assert.equal(
  buildFallbackTriggerKey("2026-07-30", "036", formalTriggerScope({ trigger_time: "21:55" })),
  "meta:fallback_trigger:2026-07-30:036:formal-21-55",
);
assert.notEqual(
  formalTriggerScope({ trigger_time: "21:55" }),
  formalTriggerScope({ trigger_time: "23:55" }),
);
