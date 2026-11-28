// Copy the web app (product/demo) into dist/ so Tauri bundles it and the window works offline.
// Only the files the app loads are copied: page, styles, script, data (index, files and bundle) and assets.
import { cpSync, mkdirSync, rmSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const demo = join(here, "..", "..", "demo");
const dist = join(here, "..", "dist");

rmSync(dist, { recursive: true, force: true });
mkdirSync(dist, { recursive: true });
for (const item of ["index.html", "styles.css", "app.js", "data.bundle.js", "data", "assets"]) {
  const from = join(demo, item);
  if (!existsSync(from)) throw new Error(`missing ${from}; run python product/demo/bundle.py first`);
  cpSync(from, join(dist, item), { recursive: true });
}
console.log(`Copied the web app into ${dist}`);
