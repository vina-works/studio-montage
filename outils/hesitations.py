"""Seconde passe de transcription pour entendre les hésitations que Whisper efface.

Sans filtre VAD et amorcée avec des « euh », elle écrit les hésitations et les reprises.
Ses mots servent à `rythme.py` : ce qui tombe dans un trou de la première passe.

Usage : python hesitations.py media.mp3 -o hesitations.json [--plages plan.json]
`--plages` limite la passe aux segments d'un plan de rythme (plus rapide).
"""
import argparse
import json
from pathlib import Path

from commun import decode, t, utf8, whisper

AMORCE = "Euh, alors, euh... hum, bah, ben, euh, c'est, c'est, on va, on va dire, euh."


def main():
    utf8()
    ap = argparse.ArgumentParser()
    ap.add_argument("media")
    ap.add_argument("-o", "--sortie", default="hesitations.json")
    ap.add_argument("--plages")
    a = ap.parse_args()
    x = decode(a.media)
    sr = 16000
    if a.plages:
        segs = json.loads(Path(a.plages).read_text(encoding="utf-8-sig"))["segments"]
        rng = sorted((t(s["debut"]) - 0.5, t(s["fin"]) + 0.5) for s in segs if not s.get("brut"))
    else:
        rng = [(0, len(x) / sr)]
    merged = []
    for lo, hi in rng:
        if merged and lo <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], hi)
        else:
            merged.append([max(0, lo), hi])
    model = whisper()
    out = []
    for lo, hi in merged:
        segs, _ = model.transcribe(x[int(lo * sr): int(hi * sr)], language="fr", word_timestamps=True, vad_filter=False,
                                   condition_on_previous_text=False, initial_prompt=AMORCE)
        for s in segs:
            for w in s.words or []:
                out.append({"w": w.word.strip(), "start": round(w.start + lo, 2), "end": round(w.end + lo, 2), "p": round(w.probability, 2)})
        print(f"{hi:.0f} s, {len(out)} mots", flush=True)
    Path(a.sortie).write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    print("OK", a.sortie)


if __name__ == "__main__":
    main()
