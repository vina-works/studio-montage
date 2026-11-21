// Active les hooks git du dépôt (.githooks/) : `node scripts/setup-hooks.mjs`.
// Silencieux et sans erreur s'il n'y a pas de dépôt git (ex. archive zip, build en CI).
import { chmodSync, existsSync, readdirSync } from "node:fs";
import { spawnSync } from "node:child_process";

if (!existsSync(".git")) process.exit(0);

const result = spawnSync("git", ["config", "core.hooksPath", ".githooks"], { stdio: "ignore" });
if (result.status !== 0) {
  console.warn("⚠️  Impossible d'activer les hooks git (git introuvable ?). Lance : git config core.hooksPath .githooks");
  process.exit(0);
}

// Les hooks doivent être exécutables (sans effet sous Windows).
for (const file of readdirSync(".githooks")) {
  try {
    chmodSync(`.githooks/${file}`, 0o755);
  } catch {
    // ignoré
  }
}
