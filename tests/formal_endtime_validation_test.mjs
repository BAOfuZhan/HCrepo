import assert from "node:assert/strict";
import worker, { validateFormalTimeWindow } from "../workers/tongyi/src/worker.js";

assert.equal(validateFormalTimeWindow("19:57", "20:00:39"), "");
assert.equal(validateFormalTimeWindow("19:57", "20:00:40"), "");
assert.equal(validateFormalTimeWindow("19:57", "20:00:43"), "");
assert.equal(validateFormalTimeWindow("19:57", "20:00:59"), "");

const html = await (await worker.fetch(new Request("http://localhost"), {}, {})).text();
assert.match(html, /的秒数小于 40，可能影响执行，确定继续吗/);
assert.match(html, /请再次确认：仍要保存正式截止时间/);
