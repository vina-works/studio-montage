// Vérifie le message d'un commit : Conventional Commits + numéro d'issue + première ligne <= 55 caractères.
// Appelé par .githooks/commit-msg avec le chemin du fichier de message (argument 1).
import { readFileSync } from "node:fs";

export const MAX_SUBJECT_LENGTH = 55;
export const TYPES = ["feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore", "revert"];

// type(scope)!: #123 description   -> scope et ! optionnels, #numéro d'issue obligatoire, description non vide
const CONVENTIONAL = new RegExp(`^(${TYPES.join("|")})(\\([a-z0-9._/-]+\\))?!?: #\\d+ \\S.*$`);

/** Retourne la liste des problèmes du sujet (vide = OK). */
export function validateSubject(subject) {
  // Messages générés par git : on ne les rejette pas.
  if (/^Merge /.test(subject) || /^Revert "/.test(subject) || /^(fixup|squash)! /.test(subject)) return [];

  const problems = [];
  const length = [...subject].length; // points de code, pas octets : "é" compte pour 1

  if (!CONVENTIONAL.test(subject)) {
    problems.push(`Format invalide. Attendu : <type>(<scope optionnel>): #<numéro d'issue> <description>   avec type parmi : ${TYPES.join(", ")}`);
  }
  if (length > MAX_SUBJECT_LENGTH) {
    problems.push(`Première ligne trop longue : ${length} caractères (maximum ${MAX_SUBJECT_LENGTH}).`);
  }
  return problems;
}

/** Première ligne utile d'un message de commit (ignore les commentaires # ajoutés par l'éditeur). */
export function extractSubject(message) {
  return (
    message
      .split(/\r?\n/)
      .find((line) => line.trim() !== "" && !line.startsWith("#")) ?? ""
  );
}

function main() {
  const file = process.argv[2];
  if (!file) {
    console.error("❌ commit-msg : chemin du fichier de message manquant.");
    process.exit(1);
  }

  const subject = extractSubject(readFileSync(file, "utf8"));
  const problems = subject === "" ? ["Message de commit vide."] : validateSubject(subject);

  if (problems.length > 0) {
    console.error("");
    console.error("❌ Commit refusé :");
    for (const problem of problems) console.error(`   - ${problem}`);
    console.error("");
    console.error(`   Ton message : "${subject}"`);
    console.error("   Exemples    : feat(admin): #42 ajoute le changement de rôle");
    console.error("                 fix: #57 corrige la redirection après login");
    console.error("   (Urgence uniquement : git commit --no-verify)");
    console.error("");
    process.exit(1);
  }
}

// N'exécute main() que si le fichier est lancé directement (pas quand il est importé pour être testé).
if (process.argv[1]?.endsWith("check-commit-msg.mjs")) main();
