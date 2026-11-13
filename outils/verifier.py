"""Vérifie un montage sans l'écouter : retranscrit et compare aux mots attendus.

Usage :
  python verifier.py edit.json transcript.json                      recolle l'audio depuis la source
  python verifier.py edit.json transcript.json --rendu video.mp4    contrôle un rendu (pistes, durée, texte)
  python verifier.py edit.json transcript.json --autour 04:38 14:26 transcrit 8 s autour de ces temps de sortie

Signale les mots manquants ou en trop, en temps de sortie. Ne dit rien de la musicalité d'un raccord :
il faut toujours écouter les raccords délicats.
"""
import argparse
import difflib
import json
import subprocess
from pathlib import Path

import numpy as np

from commun import FILL, decode, fmt, mots, norm, t, utf8, whisper

SR = 16000


def main():
    utf8()
    ap = argparse.ArgumentParser()
    ap.add_argument("edit")
    ap.add_argument("transcript")
    ap.add_argument("--rendu")
    ap.add_argument("--autour", nargs="*")
    args = ap.parse_args()
    edit = json.loads(Path(args.edit).read_text(encoding="utf-8-sig"))
    off = edit.get("offset", 0.0)
    attendu_s = sum(k["end"] - k["start"] for k in edit["keep"])
    if args.rendu:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,duration", "-of", "csv=p=0", args.rendu], capture_output=True, text=True).stdout.split()
        print("pistes :", " ".join(r), "| attendu :", f"{attendu_s:.3f} s")
        y = decode(args.rendu, SR)
    else:
        x = decode(edit["source"], SR)
        y = np.concatenate([x[int(k["start"] * SR): int(k["end"] * SR)] for k in edit["keep"]])
    print("durée audio :", f"{len(y) / SR:.2f} s")
    model = whisper()
    if args.autour:
        for a in args.autour:
            c = t(a)
            segs, _ = model.transcribe(y[max(0, int((c - 3) * SR)): int((c + 5) * SR)], language="fr", vad_filter=False, condition_on_previous_text=False)
            print(f"{a} | " + " ".join(s.text.strip() for s in segs))
        return
    segs, _ = model.transcribe(y, language="fr", word_timestamps=True, vad_filter=False, condition_on_previous_text=False)
    got = [norm(w.word) for s in segs for w in s.words or [] if norm(w.word)]
    W, _ = mots(args.transcript)
    exp, T = [], 0.0
    for k in edit["keep"]:
        fin = k.get("sous_titres_jusqu_a", k["end"])
        for w in W:
            m = (w["start"] + w["end"]) / 2 + off
            if k["start"] <= m < min(k["end"], fin) and norm(w["w"]) and norm(w["w"]) not in FILL:
                exp.append((norm(w["w"]), T + m - k["start"]))
        T += k["end"] - k["start"]
    a = [e[0] for e in exp]
    sm = difflib.SequenceMatcher(None, a, got, autojunk=False)
    print(f"mots attendus {len(a)}, entendus {len(got)}, hésitations entendues {sum(g in FILL for g in got)}, ressemblance {sm.ratio():.3f}")
    print("Écarts (beaucoup sont des variantes d'orthographe ; chercher les mots vraiment absents ou en trop) :")
    for op, i, j, k, l in sm.get_opcodes():
        if op != "equal" and j > i:
            print(f"  {fmt(exp[i][1])} {op}: {' '.join(a[i:j])} -> {' '.join(got[k:l])}")


if __name__ == "__main__":
    main()
