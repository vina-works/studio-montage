"""Salle de revue locale façon Frame.io.

Lance :  python outils/revue/serveur.py --racine "D:\\ep02" --session ep02-montage
Options : --racine <dossier de travail> (défaut : dossier courant)
          --session <nom> : une salle par conversation Claude ; ses envois vont dans
                            revue/envois/<nom>.jsonl (sans --session : revue/envois.jsonl)
          --port 8765 : premier port essayé ; s'il est pris, le suivant libre (jusqu'à +20)
          --no-browser

- Liste les vidéos et audios du dossier de travail (rendus/, tmp/, shorts/, rush/...).
- Sert les médias avec les requêtes Range (lecture et saut instantanés, même sur 300 Mo).
- Miniatures et métadonnées via ffmpeg/ffprobe (cache dans <racine>/tmp/revue_cache/).
- Commentaires enregistrés dans <racine>/revue/commentaires/<chemin>.json, plus un .md
  lisible (c'est ce fichier que Claude lit pour en tirer un plan de coupe).
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.parse
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ICI = Path(__file__).resolve().parent  # index.html
RACINE = Path.cwd().resolve()  # dossier de travail, fixé par --racine dans main()
COMMENTAIRES = RACINE / "revue" / "commentaires"
SAUVEGARDES = RACINE / "revue" / "sauvegardes"
ENVOIS = RACINE / "revue" / "envois.jsonl"
CACHE = RACINE / "tmp" / "revue_cache"
SESSION = ""  # nom de la conversation Claude reliée à cette salle
MONTAGES = RACINE / "revue" / "montage"  # retouches manuelles du montage (timeline)


def fixer_racine(dossier: str, session: str = "") -> None:
    global RACINE, COMMENTAIRES, SAUVEGARDES, ENVOIS, CACHE, SESSION, MONTAGES
    RACINE = Path(dossier).resolve()
    SESSION = session
    COMMENTAIRES = RACINE / "revue" / "commentaires"
    SAUVEGARDES = RACINE / "revue" / "sauvegardes"
    if session:
        ENVOIS = RACINE / "revue" / "envois" / f"{session}.jsonl"
    else:
        ENVOIS = RACINE / "revue" / "envois.jsonl"
    CACHE = RACINE / "tmp" / "revue_cache"
    MONTAGES = RACINE / "revue" / "montage"


def nom_session(brut: str) -> str:
    nom = re.sub(r"[^\w\-]+", "-", brut.strip()).strip("-")[:60]
    if brut and not nom:
        sys.exit("Nom de session invalide : lettres, chiffres, - et _ seulement.")
    return nom


_verrou_envois = threading.Lock()


def enregistrer_envoi(rel: str, message: str) -> dict:
    """Ajoute une ligne à revue/envois.jsonl : Claude surveille ce fichier."""
    f = fichier_commentaires(rel)
    elements = json.loads(f.read_text(encoding="utf-8")) if f.exists() else []
    moments = sum(1 for c in elements if c.get("type") == "moment")
    comms = [c for c in elements if c.get("type") != "moment"]
    envoi = {
        "envoi": time.strftime("%Y-%m-%d %H:%M:%S"),
        "session": SESSION or None,
        "media": rel,
        "message": message.replace("\n", " ").strip()[:2000],
        "commentaires_ouverts": sum(1 for c in comms if not c.get("resolu")),
        "commentaires": len(comms),
        "moments": moments,
        "fichier": rel_de(f.with_suffix(".md")) if f.exists() else None,
    }
    with _verrou_envois:
        ENVOIS.parent.mkdir(parents=True, exist_ok=True)
        with open(ENVOIS, "a", encoding="utf-8") as out:
            out.write(json.dumps(envoi, ensure_ascii=False) + "\n")
    return envoi


CATEGORIES = {"fort": "Moment fort", "short": "Idée de short", "citation": "Citation",
              "rire": "Rire", "couper": "À couper"}


EXTS_VIDEO = {".mp4", ".mov", ".m4v", ".webm", ".mkv"}
EXTS_AUDIO = {".m4a", ".mp3", ".wav", ".aac", ".ogg", ".flac"}
EXTS = EXTS_VIDEO | EXTS_AUDIO
IGNORES = {".claude", "revue", ".git", "node_modules", "revue_cache"}

mimetypes.add_type("video/mp4", ".mp4")
mimetypes.add_type("video/mp4", ".m4v")
mimetypes.add_type("audio/mp4", ".m4a")
mimetypes.add_type("text/vtt", ".vtt")

_verrou_meta = threading.Lock()


def chemin_sur(rel: str) -> Path | None:
    """Résout un chemin relatif au projet sans permettre d'en sortir."""
    if not rel:
        return None
    p = (RACINE / urllib.parse.unquote(rel)).resolve()
    try:
        p.relative_to(RACINE)
    except ValueError:
        return None
    return p


def rel_de(p: Path) -> str:
    return p.relative_to(RACINE).as_posix()


def fichier_commentaires(rel: str) -> Path:
    nom = re.sub(r"[^\w.\-]+", "__", rel)
    return COMMENTAIRES / f"{nom}.json"


def lister_medias() -> list[Path]:
    out = []
    for dossier, sous, fichiers in os.walk(RACINE):
        sous[:] = sorted(d for d in sous if d not in IGNORES and not d.startswith("."))
        for f in sorted(fichiers):
            if Path(f).suffix.lower() in EXTS:
                out.append(Path(dossier) / f)
    return out


def _charger_cache_meta() -> dict:
    f = CACHE / "meta.json"
    if f.exists():
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def meta(p: Path, cache: dict) -> dict:
    st = p.stat()
    cle = rel_de(p)
    signature = f"{st.st_size}-{int(st.st_mtime)}"
    if cle in cache and cache[cle].get("sig") == signature:
        return cache[cle]
    info = {"sig": signature, "duree": 0, "fps": 25, "largeur": 0, "hauteur": 0}
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries",
             "format=duration:stream=codec_type,width,height,r_frame_rate",
             "-of", "json", str(p)],
            capture_output=True, text=True, timeout=30,
        )
        d = json.loads(r.stdout or "{}")
        info["duree"] = float(d.get("format", {}).get("duration", 0) or 0)
        for s in d.get("streams", []):
            if s.get("codec_type") == "video" and s.get("width"):
                info["largeur"], info["hauteur"] = s["width"], s["height"]
                num, _, den = (s.get("r_frame_rate") or "25/1").partition("/")
                try:
                    info["fps"] = round(float(num) / float(den or 1), 3)
                except ZeroDivisionError:
                    pass
                break
    except Exception as e:  # ffprobe absent ou fichier illisible
        info["erreur"] = str(e)
    cache[cle] = info
    return info


def liste_assets() -> list[dict]:
    with _verrou_meta:
        cache = _charger_cache_meta()
        assets = []
        for p in lister_medias():
            m = meta(p, cache)
            rel = rel_de(p)
            nb, ouverts, moments = 0, 0, 0
            fc = fichier_commentaires(rel)
            if fc.exists():
                try:
                    cs = json.loads(fc.read_text(encoding="utf-8"))
                    moments = sum(1 for c in cs if c.get("type") == "moment")
                    cs = [c for c in cs if c.get("type") != "moment"]
                    nb = len(cs)
                    ouverts = sum(1 for c in cs if not c.get("resolu"))
                except Exception:
                    pass
            srt = p.with_suffix(".srt")
            assets.append({
                "chemin": rel,
                "nom": p.name,
                "dossier": rel_de(p.parent) if p.parent != RACINE else "",
                "taille": p.stat().st_size,
                "modifie": p.stat().st_mtime,
                "audio": p.suffix.lower() in EXTS_AUDIO,
                "srt": rel_de(srt) if srt.exists() else None,
                "commentaires": nb,
                "ouverts": ouverts,
                "moments": moments,
                "absolu": str(p),
                **{k: m.get(k) for k in ("duree", "fps", "largeur", "hauteur")},
            })
        CACHE.mkdir(parents=True, exist_ok=True)
        (CACHE / "meta.json").write_text(json.dumps(cache, indent=1), encoding="utf-8")
    return assets


def miniature(p: Path, t: float | None = None) -> Path | None:
    CACHE.mkdir(parents=True, exist_ok=True)
    st = p.stat()
    tag = "" if t is None else f"_{t:.1f}"
    out = CACHE / (re.sub(r"[^\w.\-]+", "__", rel_de(p)) + f"_{st.st_size}{tag}.jpg")
    if out.exists():
        return out
    if t is None:
        dur = meta(p, _charger_cache_meta()).get("duree") or 0
        t = min(5.0, dur * 0.1) if dur else 1.0
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", str(p),
             "-frames:v", "1", "-vf", "scale=480:-2", "-q:v", "4", str(out)],
            capture_output=True, timeout=30,
        )
    except Exception:
        return None
    return out if out.exists() else None


def srt_vers_vtt(texte: str) -> str:
    texte = texte.replace("\r\n", "\n").lstrip("﻿")
    texte = re.sub(r"(\d{2}:\d{2}:\d{2}),(\d{3})", r"\1.\2", texte)
    return "WEBVTT\n\n" + texte


def tc(s: float, fps: float = 25) -> str:
    s = max(0.0, float(s))
    h, m = int(s // 3600), int(s % 3600 // 60)
    sec = int(s % 60)
    return f"{h:02d}:{m:02d}:{sec:02d}" if h else f"{m:02d}:{sec:02d}"


def _borne(c: dict) -> str:
    if c.get("t") is None:
        return "général"
    b = tc(c["t"])
    if c.get("fin") is not None:
        b += f" → {tc(c['fin'])}"
    secondes = f"{c['t']:.2f} s" + (f" → {c['fin']:.2f} s" if c.get("fin") is not None else "")
    return f"**{b}** ({secondes})"


def _ordre(c: dict) -> float:
    return c["t"] if isinstance(c.get("t"), (int, float)) else 1e12


def ecrire_markdown(rel: str, elements: list[dict]) -> None:
    comms = sorted((c for c in elements if c.get("type") != "moment"), key=_ordre)
    moments = sorted((c for c in elements if c.get("type") == "moment"), key=_ordre)
    lignes = [f"# Revue : {rel}", ""]
    if moments:
        lignes += ["## Moments forts", ""]
        for m in moments:
            cat = CATEGORIES.get(m.get("cat"), m.get("cat") or "Moment fort")
            note = f", note {m['note']}/3" if m.get("note") else ""
            titre = (m.get("texte") or "").strip()
            lignes.append(f"- {_borne(m)} [{cat}{note}]{' : ' + titre if titre else ''}")
        lignes.append("")
    lignes += ["## Commentaires", ""]
    for c in comms:
        etat = "x" if c.get("resolu") else " "
        dessin = " (avec dessin)" if c.get("dessin") else ""
        lignes.append(f"- [{etat}] {_borne(c)}, {c.get('auteur', '?')} : "
                      f"{(c.get('texte') or '').strip()}{dessin}")
        for r in c.get("reponses") or []:
            lignes.append(f"    - {r.get('auteur', '?')} : {(r.get('texte') or '').strip()}")
    if not comms:
        lignes.append("(aucun)")
    fichier_commentaires(rel).with_suffix(".md").write_text("\n".join(lignes) + "\n", encoding="utf-8")


def sauvegarder(rel: str) -> Path | None:
    """Copie horodatée du fichier de revue dans revue/sauvegardes/."""
    f = fichier_commentaires(rel)
    if not f.exists():
        return None
    SAUVEGARDES.mkdir(parents=True, exist_ok=True)
    horodatage = time.strftime("%Y%m%d-%H%M%S")
    dest = SAUVEGARDES / f"{f.stem}__{horodatage}.json"
    shutil.copy2(f, dest)
    return dest


EXTS_IMG = {".png", ".jpg", ".jpeg", ".webp"}
mimetypes.add_type("image/webp", ".webp")


def plans_de_coupe() -> list[str]:
    """edit*.json à la racine du dossier de travail (un plan de coupe par fichier)."""
    plans = [p for p in RACINE.glob("edit*.json")
             if p.is_file() and not p.name.endswith((".overlays.json", ".manuel.json"))]
    return [p.name for p in sorted(plans, key=lambda p: p.stat().st_mtime, reverse=True)]  # le plus récent d'abord


def fichier_plan(rel: str) -> Path | None:
    p = chemin_sur(rel)
    if not p or p.parent != RACINE or not p.is_file() or p.suffix.lower() != ".json" or not p.name.startswith("edit"):
        return None
    return p


def montage_manuel(p: Path) -> Path:
    return MONTAGES / f"{p.stem}.manuel.json"


def lire_json(f: Path):
    try:
        return json.loads(f.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def lire_plan(p: Path):
    """Plan de coupe où chaque segment porte sa source, en chemin relatif au dossier de travail.

    Accepte aussi le format à une seule source (`source` en tête de fichier, chemin absolu ou relatif) :
    les segments sans `source` la reçoivent.
    """
    d = lire_json(p)
    if not isinstance(d, dict) or not isinstance(d.get("keep"), list):
        return d
    src = d.get("source")
    if isinstance(src, str) and src:
        s = Path(src) if Path(src).is_absolute() else RACINE / src
        try:
            src = s.resolve().relative_to(RACINE).as_posix()
        except ValueError:
            pass
        for k in d["keep"]:
            if isinstance(k, dict) and not k.get("source"):
                k["source"] = src
    return d


def mots_transcription(p: Path) -> list:
    """[[mot, debut, fin], ...] depuis <media>.transcript.json (timestamps au mot)."""
    d = lire_json(p.with_suffix(".transcript.json")) or {}
    out = []
    for s in d.get("segments", []):
        for w in s.get("words", []):
            out.append([w.get("w", ""), w.get("start", 0), w.get("end", 0)])
    return out



def _mise_en_page(plan: dict, fps: int = 60) -> list[tuple]:
    """(source, debut_source, sortie, duree) de chaque plan, quantifiés à l'image comme au rendu."""
    out, o = [], 0.0
    for k in plan.get("keep", []):
        a = round(k["start"] * fps) / fps
        n = max(1, round((k["end"] - k["start"]) * fps))
        out.append((k["source"], a, o, n / fps))
        o += n / fps
    return out


def _vers_source(couches: list[tuple], t: float):
    for src, a, o, d in couches:
        if o <= t < o + d:
            return src, round(a + (t - o), 3)
    return None


def reperes() -> list[dict]:
    """Commentaires, moments forts et repères posés dans la salle, ramenés au temps de la prise source.

    Un plan de coupe (edit*.json) peut lister ses rendus dans "rendus" : les timecodes d'un rendu sont
    reconvertis en temps source avec ce plan ; ceux d'une source sont repris tels quels.
    """
    plans = [(p, lire_plan(p)) for p in RACINE.glob("edit*.json")
             if p.is_file() and not p.name.endswith((".overlays.json", ".manuel.json"))]
    medias: dict[str, tuple] = {}
    for p, d in plans:
        if not isinstance(d, dict) or not isinstance(d.get("keep"), list):
            continue
        for src in d.get("sources") or sorted({k.get("source") for k in d["keep"] if isinstance(k, dict) and k.get("source")}):
            medias.setdefault(src, ("source", None))
        for rel in d.get("rendus", []):
            medias.setdefault(rel, ("rendu", _mise_en_page(d)))
    out = []
    for rel, (origine, couches) in medias.items():
        f = fichier_commentaires(rel)
        elements = lire_json(f) if f.exists() else None
        for c in elements or []:
            t = c.get("t")
            if not isinstance(t, (int, float)):
                continue
            if origine == "source":
                pos, fin = (rel, t), (rel, c["fin"]) if isinstance(c.get("fin"), (int, float)) else None
            else:
                pos = _vers_source(couches, t)
                fin = _vers_source(couches, c["fin"]) if isinstance(c.get("fin"), (int, float)) else None
                if pos is None:
                    continue
            r = {"id": c.get("id"), "media": rel, "origine": origine, "type": c.get("type") or "commentaire",
                 "cat": c.get("cat"), "note": c.get("note"), "src": pos[0], "at": pos[1],
                 "texte": c.get("texte") or "", "auteur": c.get("auteur") or "", "resolu": bool(c.get("resolu")), "t": t}
            if fin and fin[0] == pos[0]:
                r["at_fin"] = fin[1]
            out.append(r)
    return out


def valider_montage(d) -> bool:
    if not isinstance(d, dict) or not isinstance(d.get("keep"), list) or not d["keep"]:
        return False
    for k in d["keep"]:
        if not (isinstance(k, dict) and isinstance(k.get("source"), str)
                and isinstance(k.get("start"), (int, float)) and isinstance(k.get("end"), (int, float))
                and 0 <= k["start"] < k["end"]):
            return False
    return isinstance(d.get("overlays", []), list)



class Gestionnaire(BaseHTTPRequestHandler):
    server_version = "Revue/1.0"

    def log_message(self, fmt, *args):  # journal discret
        if "/media" not in self.path and "/thumb" not in self.path:
            sys.stderr.write("· " + (fmt % args) + "\n")

    # ---------- utilitaires ----------
    def _json(self, obj, code=200):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _fichier(self, p: Path, ctype: str | None = None, cache="no-cache"):
        taille = p.stat().st_size
        ctype = ctype or mimetypes.guess_type(p.name)[0] or "application/octet-stream"
        plage = self.headers.get("Range")
        debut, fin = 0, taille - 1
        if plage:
            m = re.match(r"bytes=(\d*)-(\d*)", plage)
            if m:
                if m.group(1):
                    debut = int(m.group(1))
                    if m.group(2):
                        fin = min(int(m.group(2)), taille - 1)
                elif m.group(2):
                    debut = max(0, taille - int(m.group(2)))
            if debut > fin or debut >= taille:
                self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                self.send_header("Content-Range", f"bytes */{taille}")
                self.end_headers()
                return
            self.send_response(HTTPStatus.PARTIAL_CONTENT)
            self.send_header("Content-Range", f"bytes {debut}-{fin}/{taille}")
        else:
            self.send_response(HTTPStatus.OK)
        longueur = fin - debut + 1
        self.send_header("Content-Type", ctype)
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(longueur))
        self.send_header("Cache-Control", cache)
        self.end_headers()
        if self.command == "HEAD":
            return
        try:
            with open(p, "rb") as f:
                f.seek(debut)
                reste = longueur
                while reste > 0:
                    bloc = f.read(min(1024 * 512, reste))
                    if not bloc:
                        break
                    self.wfile.write(bloc)
                    reste -= len(bloc)
        except (ConnectionResetError, BrokenPipeError, ConnectionAbortedError):
            pass  # le navigateur annule les plages quand on saute dans la vidéo

    # ---------- routes ----------
    def do_HEAD(self):
        self.do_GET()

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        rel = (urllib.parse.parse_qs(url.query).get("p") or [""])[0]
        if url.path not in ("/api/sauvegarde", "/api/envoyer"):
            return self.send_error(404)
        p = chemin_sur(rel)
        if not p or not p.is_file():
            return self.send_error(400, "média inconnu")
        if url.path == "/api/envoyer":
            n = int(self.headers.get("Content-Length") or 0)
            try:
                corps = json.loads(self.rfile.read(n).decode("utf-8") or "{}")
            except Exception:
                return self.send_error(400, "JSON invalide")
            return self._json({"ok": True, **enregistrer_envoi(rel, str(corps.get("message") or ""))})
        dest = sauvegarder(rel)
        if dest is None:
            return self._json({"ok": False, "erreur": "rien à sauvegarder"})
        return self._json({"ok": True, "fichier": rel_de(dest)})

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(url.query)
        rel = (q.get("p") or [""])[0]

        if url.path in ("/", "/index.html"):
            return self._fichier(ICI / "index.html", "text/html; charset=utf-8")
        if url.path in ("/montage.js", "/montage.css"):
            return self._fichier(ICI / url.path.lstrip("/"),
                                 "text/javascript; charset=utf-8" if url.path.endswith(".js") else "text/css; charset=utf-8")
        if url.path == "/api/montages":
            return self._json(plans_de_coupe())
        if url.path == "/api/montage":
            p = fichier_plan(rel)
            if not p:
                return self.send_error(400, "plan de coupe inconnu")
            m = montage_manuel(p)
            return self._json({
                "edit": lire_plan(p),
                "overlays": lire_json(p.with_name(p.stem + ".overlays.json")),
                "manuel": lire_json(m) if m.exists() else None,
                "reperes": reperes(),
            })
        if url.path == "/api/transcript":
            p = chemin_sur(rel)
            if p and p.is_file() and p.suffix.lower() in EXTS:
                return self._json(mots_transcription(p))
            return self.send_error(404)
        if url.path == "/img":
            p = chemin_sur(rel)
            if p and p.is_file() and p.suffix.lower() in EXTS_IMG:
                return self._fichier(p)
            return self.send_error(404)
        if url.path == "/api/assets":
            return self._json(liste_assets())
        if url.path == "/api/info":
            return self._json({"session": SESSION or None, "racine": str(RACINE),
                               "envois": rel_de(ENVOIS)})
        if url.path == "/api/commentaires":
            f = fichier_commentaires(rel)
            return self._json(json.loads(f.read_text(encoding="utf-8")) if f.exists() else [])
        if url.path == "/media":
            p = chemin_sur(rel)
            if p and p.is_file() and p.suffix.lower() in EXTS:
                return self._fichier(p)
        if url.path == "/thumb":
            p = chemin_sur(rel)
            if p and p.is_file() and p.suffix.lower() in EXTS_VIDEO:
                t = (q.get("t") or [None])[0]
                m = miniature(p, float(t) if t else None)
                if m:
                    return self._fichier(m, "image/jpeg", cache="max-age=86400")
        if url.path == "/vtt":
            p = chemin_sur(rel)
            if p and p.is_file() and p.suffix.lower() == ".srt":
                data = srt_vers_vtt(p.read_text(encoding="utf-8", errors="replace")).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/vtt; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                if self.command != "HEAD":
                    self.wfile.write(data)
                return
        self.send_error(404)

    def do_PUT(self):
        url = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(url.query)
        rel = (q.get("p") or [""])[0]
        if url.path == "/api/montage":
            plan = fichier_plan(rel)
            if not plan:
                return self.send_error(400, "plan de coupe inconnu")
            n = int(self.headers.get("Content-Length") or 0)
            try:
                d = json.loads(self.rfile.read(n).decode("utf-8"))
            except Exception:
                return self.send_error(400, "JSON invalide")
            if not valider_montage(d):
                return self.send_error(400, "montage invalide")
            MONTAGES.mkdir(parents=True, exist_ok=True)
            f = montage_manuel(plan)
            tmp = f.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
            os.replace(tmp, f)
            copie = None
            if (q.get("copie") or [""])[0]:
                SAUVEGARDES.mkdir(parents=True, exist_ok=True)
                copie = SAUVEGARDES / f"{f.stem}__{time.strftime('%Y%m%d-%H%M%S')}.json"
                shutil.copy2(f, copie)
            return self._json({"ok": True, "fichier": rel_de(f), "n": len(d["keep"]),
                               "copie": rel_de(copie) if copie else None})
        if url.path != "/api/commentaires":
            return self.send_error(404)
        p = chemin_sur(rel)
        if not p or not p.is_file():
            return self.send_error(400, "média inconnu")
        n = int(self.headers.get("Content-Length") or 0)
        try:
            comms = json.loads(self.rfile.read(n).decode("utf-8"))
            assert isinstance(comms, list)
        except Exception:
            return self.send_error(400, "JSON invalide")
        COMMENTAIRES.mkdir(parents=True, exist_ok=True)
        f = fichier_commentaires(rel)
        tmp = f.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(comms, ensure_ascii=False, indent=1), encoding="utf-8")
        os.replace(tmp, f)
        ecrire_markdown(rel, comms)
        self._json({"ok": True, "n": len(comms)})


class ServeurExclusif(ThreadingHTTPServer):
    """Refuse un port déjà pris : sous Windows, SO_REUSEADDR laisserait deux salles l'écouter."""
    allow_reuse_address = False
    daemon_threads = True

    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--racine", default=".", help="dossier de travail qui contient les médias")
    ap.add_argument("--session", default="", help="nom de la conversation Claude reliée à cette salle")
    ap.add_argument("--port", type=int, default=8765, help="premier port essayé")
    ap.add_argument("--port-exact", action="store_true", help="échouer si --port est pris au lieu d'essayer le suivant")
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args()
    if not Path(a.racine).is_dir():
        sys.exit(f"Dossier introuvable : {a.racine}")
    fixer_racine(a.racine, nom_session(a.session))
    ENVOIS.parent.mkdir(parents=True, exist_ok=True)
    ENVOIS.touch(exist_ok=True)  # pour que Claude puisse le surveiller dès le départ
    print(f"Dossier de travail : {RACINE}")
    print(f"Conversation : {SESSION or '(aucune)'}   envois : {ENVOIS}")
    srv, port = None, a.port
    for port in [a.port] if a.port_exact else range(a.port, a.port + 21):
        try:
            srv = ServeurExclusif(("127.0.0.1", port), Gestionnaire)
            break
        except OSError:
            continue
    if srv is None:
        sys.exit(f"Le port {a.port} est déjà pris (une autre salle tourne ?). Fermer l'autre ou changer --port."
                 if a.port_exact else f"Aucun port libre entre {a.port} et {a.port + 20}.")
    url = f"http://localhost:{port}"
    print(f"Salle de revue : {url}   (Ctrl+C pour arrêter)", flush=True)
    if not a.no_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
