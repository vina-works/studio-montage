// Signale dans les fichiers de contenu les caractères interdits par la règle commune
// « style d'écriture » (voir AGENTS.md) : emoji, point médian (U+00B7), tiret cadratin (U+2014).
//   node scripts/check-style.mjs [--strict] [fichiers...]
// Sans fichiers : tous les fichiers suivis par git avec une extension de contenu.
// Par défaut : signale et sort avec 0 (avertissement). Avec --strict : sort avec 1 s'il y a un problème.
// Pour tolérer une ligne précise (citation, exemple) : y ajouter le texte `style-ok`.
import { readFileSync } from "node:fs";
import { spawnSync } from "node:child_process";

const CONTENT = /\.(md|mdx|txt|html|htm)$/i;
const argv = process.argv.slice(2);
const strict = argv.includes("--strict");
let files = argv.filter((a) => !a.startsWith("--"));
if (files.length === 0) {
  files = spawnSync("git", ["ls-files"], { encoding: "utf8" }).stdout.split("\n").filter(Boolean);
}
files = files.filter((f) => CONTENT.test(f) && !f.includes("node_modules/"));

const FORBIDDEN = [
  { re: /·/gu, label: "point médian (·)" },
  { re: /—/gu, label: "tiret cadratin (—)" },
  { re: /\p{Extended_Pictographic}/gu, label: "emoji", ignore: new Set(["©", "®", "™"]) },
];

let count = 0;
for (const file of files) {
  let text;
  try {
    text = readFileSync(file, "utf8");
  } catch {
    continue; // fichier supprimé ou illisible
  }
  text.split(/\r?\n/).forEach((line, i) => {
    if (line.includes("style-ok")) return;
    for (const { re, label, ignore } of FORBIDDEN) {
      for (const m of line.matchAll(re)) {
        if (ignore?.has(m[0])) continue;
        console.log(`${file}:${i + 1}:${m.index + 1}  ${label}`);
        count++;
      }
    }
  });
}

if (count > 0) {
  console.error(`\n⚠️  ${count} caractère(s) interdit(s) par la règle de style d'écriture (voir AGENTS.md).`);
  if (strict) process.exit(1);
}
