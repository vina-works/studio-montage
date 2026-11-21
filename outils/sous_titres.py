"""Sous-titres .srt de la vidéo montée, recalculés depuis edit.json (jamais le .srt d'origine).

Usage : python sous_titres.py edit.json transcript.json -o video.srt
`offset` de edit.json convertit les temps de la transcription vers la source vidéo.
"""
import argparse
import json
from pathlib import Path

from commun import FILL, appliquer_glossaire, glossaire, mots, noms_propres, norm, utf8

PROPRES = noms_propres()


def joindre(ws, regles):
    s = ""
    for i, w in enumerate(ws):
        tok = w["w"]
        if i and tok in ("?", "!", "%"):
            s += " "
        elif i and not tok.startswith(("'", "-")):
            s += " "
        if i and tok[:1].isupper() and tok.strip(",?.") not in PROPRES and not tok.isupper():
            tok = tok[0].lower() + tok[1:]
        s += tok
    s = appliquer_glossaire(s, regles)
    return s[:1].upper() + s[1:]


def ts(x):
    h, r = divmod(x, 3600)
    m, s = divmod(r, 60)
    return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s % 1) * 1000):03d}"


def couper(s, n=40):
    if len(s) <= n:
        return s
    sp = [i for i, c in enumerate(s) if c == " "]
    i = min(sp, key=lambda p: abs(p - len(s) // 2))
    return s[:i] + "\n" + s[i + 1:]


def main():
    utf8()
    ap = argparse.ArgumentParser()
    ap.add_argument("edit")
    ap.add_argument("transcript")
    ap.add_argument("-o", "--sortie", required=True)
    args = ap.parse_args()
    edit = json.loads(Path(args.edit).read_text(encoding="utf-8-sig"))
    off = edit.get("offset", 0.0)
    W, _ = mots(args.transcript)
    regles = glossaire()
    items, T = [], 0.0
    for k in edit["keep"]:
        fin_texte = k.get("sous_titres_jusqu_a", k["end"])
        for w in W:
            m = (w["start"] + w["end"]) / 2 + off
            if k["start"] <= m < min(k["end"], fin_texte) and norm(w["w"]) not in FILL:
                items.append({"w": w["w"], "seg": w["seg"], "a": T + max(0, w["start"] + off - k["start"]), "z": T + min(k["end"] - k["start"], w["end"] + off - k["start"])})
        T += k["end"] - k["start"]
    cues, cur = [], []
    for w in items:
        if cur:
            colle = w["w"].startswith(("'", "-", "?", "%", "!"))
            n = len(joindre(cur + [w], regles))
            phrase = w["seg"] != cur[-1]["seg"] and n > 30
            if not colle and (w["a"] - cur[-1]["z"] > 0.45 or n > 74 or phrase or w["z"] - cur[0]["a"] > 5.5):
                cues.append(cur)
                cur = []
        cur.append(w)
    if cur:
        cues.append(cur)
    out = []
    for i, c in enumerate(cues):
        z = c[-1]["z"] + 0.15
        if i + 1 < len(cues):
            z = min(z, cues[i + 1][0]["a"] - 0.01)
        out.append(f"{i + 1}\n{ts(c[0]['a'])} --> {ts(max(z, c[0]['a'] + 0.4))}\n{couper(joindre(c, regles))}\n")
    Path(args.sortie).write_text("\n".join(out), encoding="utf-8")
    print(f"OK {args.sortie} : {len(cues)} sous-titres, dernier à {ts(cues[-1][-1]['z'])}, montage de {ts(T)}")


if __name__ == "__main__":
    main()
