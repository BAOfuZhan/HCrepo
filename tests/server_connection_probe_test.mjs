import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import worker, { cloudflareServerFetchUrl } from "../workers/tongyi/src/worker.js";

assert.equal(
  cloudflareServerFetchUrl("http://62.234.222.77/dispatch"),
  "https://renewal-api.baofuzhang.me/api/internal/server-dispatch-proxy",
);
assert.equal(
  cloudflareServerFetchUrl("https://seat.example.com/dispatch"),
  "https://seat.example.com/dispatch",
);

const html = await (await worker.fetch(new Request("http://localhost"), {}, {})).text();
assert.match(html, /服务器连接：正常/);
assert.match(html, /服务器连接：失败/);
assert.match(html, /学校已保存，但/);
const source = await readFile(new URL("../workers/tongyi/src/worker.js", import.meta.url), "utf8");
assert.match(source, /DEFAULT_SERVER_DISPATCH_PROXY_URL/);
assert.match(source, /serverApiKey: apiKey/);
