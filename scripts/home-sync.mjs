// Synchronise la config de base depuis vina-works/repo-home vers le dépôt courant.
//   node scripts/home-sync.mjs [--dry-run] [--ref <branche|tag>]
// - fichiers listés dans .home/managed.txt : toujours écrasés ;
// - fichiers listés dans .home/seed.txt    : copiés seulement s'ils n'existent pas ;
// - .home/version : mémorise le commit de repo-home appliqué.
// Ne committe rien : relis `git diff`, puis committe toi-même.
// Variable HOME_REPO pour changer la source (défaut : vina-works/repo-home).
import { spawnSync } from "node:child_process";
import { cpSync, existsSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync, statSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";

const args = process.argv.slice(2);
const dryRun = args.includes("--dry-run");
const ref = args.includes("--ref") ? args[args.indexOf("--ref") + 1] : undefined;
const repo = process.env.HOME_REPO ?? "vina-works/repo-home";

const run = (cmd, cmdArgs, opts = {}) => spawnSync(cmd, cmdArgs, { encoding: "utf8", ...opts });
const list = (file) =>
  readFileSync(file, "utf8").split("\n").map((l) => l.trim()).filter((l) => l && !l.startsWith("#"));

const tmp = mkdtempSync(join(tmpdir(), "repo-home-"));
try {
  // HTTPS + identifiants de gh : marche quel que soit le protocole configuré dans gh.
  const clone = run("git", [
    "-c", "credential.helper=", "-c", "credential.helper=!gh auth git-credential",
    "clone", "--quiet", "--depth", "1", ...(ref ? ["--branch", ref] : []),
    `https://github.com/${repo}.git`, tmp,
  ], { stdio: ["ignore", "inherit", "inherit"] });
  if (clone.status !== 0) {
    console.error(`❌ Impossible de cloner ${repo} (gh auth login fait ? accès au dépôt ?).`);
    process.exit(1);
  }
  const sha = run("git", ["-C", tmp, "rev-parse", "--short", "HEAD"]).stdout.trim();

  const files = (rel) => {
    const abs = join(tmp, rel);
    if (!existsSync(abs)) return [];
    if (!statSync(abs).isDirectory()) return [rel];
    return readdirSync(abs, { recursive: true, withFileTypes: true })
      .filter((e) => e.isFile())
      .map((e) => join(e.parentPath ?? e.path, e.name).slice(tmp.length + 1));
  };

  const copy = (rel) => {
    console.log(`${dryRun ? "[dry-run] " : ""}${existsSync(rel) ? "maj  " : "ajout"} ${rel}`);
    if (dryRun) return;
    mkdirSync(dirname(rel), { recursive: true });
    cpSync(join(tmp, rel), rel);
  };

  for (const entry of list(join(tmp, ".home/managed.txt"))) files(entry).forEach(copy);
  for (const entry of list(join(tmp, ".home/seed.txt"))) {
    for (const rel of files(entry)) {
      if (existsSync(rel)) console.log(`garde ${rel} (déjà présent, appartient à ce dépôt)`);
      else copy(rel);
    }
  }

  if (!dryRun) {
    writeFileSync(".home/version", `${repo}@${sha}\n`);
    run("node", ["scripts/setup-hooks.mjs"], { stdio: "inherit" });
    console.log(`\n✅ Synchronisé avec ${repo}@${sha}. Relis \`git diff\`, puis committe.`);
  }
} finally {
  rmSync(tmp, { recursive: true, force: true });
}
