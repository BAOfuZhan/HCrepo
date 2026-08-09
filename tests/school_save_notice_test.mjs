import assert from "node:assert/strict";
import worker from "../workers/tongyi/src/worker.js";

const html = await (await worker.fetch(new Request("http://localhost"), {}, {})).text();
const source = html.slice(
  html.indexOf("function schoolNoticeValue"),
  html.indexOf("function setUserSavePending"),
);
const buildSchoolSaveNotice = Function(`${source}; return buildSchoolSaveNotice;`)();

assert.equal(
  buildSchoolSaveNotice(
    { trigger_time: "19:57", enable_slider: false, strategy: {} },
    { trigger_time: "19:58", enable_slider: true, strategy: {}, config_revision: 3 },
  ),
  "学校配置已生效（版本 3）\n开始时间：19:57 → 19:58\n滑块验证码：关闭 → 开启",
);
assert.equal(
  buildSchoolSaveNotice(
    { trigger_time: "19:57", strategy: {} },
    { trigger_time: "19:57", strategy: {}, config_revision: 3 },
  ),
  "学校配置未修改",
);
assert.equal(
  buildSchoolSaveNotice(
    { strategy: { fast_probe_start_range_ms: [8, 20] } },
    { strategy: { fast_probe_start_range_ms: [9, 21] }, config_revision: 4 },
  ),
  "学校配置已生效（版本 4）\n快速探测范围：8,20 → 9,21",
);
assert.match(html, /school-save-notice/);
