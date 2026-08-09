import assert from "node:assert/strict";
import worker, { resolveUserTopModeForSchool } from "../workers/tongyi/src/worker.js";

const schoolA = { endtime: "19:00:40", strategy: { mode: "A" } };

assert.equal(resolveUserTopModeForSchool(schoolA), "A");
assert.equal(resolveUserTopModeForSchool(schoolA, "19:00:40"), "A");
assert.equal(resolveUserTopModeForSchool(schoolA, "19:00:41"), "A");
assert.equal(resolveUserTopModeForSchool(schoolA, "19:00:40", "B"), "B");
assert.equal(resolveUserTopModeForSchool(schoolA, "19:00:40", "C"), "C");

const html = await (await worker.fetch(new Request("http://localhost"), {}, {})).text();
assert.match(html, /目标秒数为 00，仍将按策略 A 执行。/);
assert.match(html, /目标秒数为 00，仍按策略 A 执行/);
