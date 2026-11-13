"""Qui parle sur un intervalle ? Empreinte spectrale (log-mel) comparée à des passages de référence.

Usage : python qui_parle.py media.mp4 refs.json intervalles.json
  refs.json        {"Alice": [[38.2, 70.0], ...], "Bruno": [...]}   passages sûrs, temps du média
  intervalles.json [[début, fin], ...] ou {"nom": [[début, fin], ...]}

Indice, pas preuve : un score sous 0,3 est peu fiable. Croiser avec les plans (le montage cadre
souvent la personne qui parle). Les références sont d'abord validées sur d'autres passages sûrs.
"""
import argparse
import json
from pathlib import Path

import numpy as np

from commun import decode, utf8

SR, NF, HOP, NM = 16000, 512, 160, 40


def banc_mel():
    f = np.linspace(0, SR / 2, NF // 2 + 1)
    mel = lambda x: 2595 * np.log10(1 + x / 700)
    hz = 700 * (10 ** (np.linspace(mel(60), mel(7000), NM + 2) / 2595) - 1)
    fb = np.zeros((NM, len(f)))
    for i in range(NM):
        fb[i] = np.clip(np.minimum((f - hz[i]) / (hz[i + 1] - hz[i]), (hz[i + 2] - f) / (hz[i + 2] - hz[i + 1])), 0, None)
    return fb


FB, WIN = banc_mel(), np.hanning(NF)


def empreinte(x, a, z):
    s = x[int(a * SR): int(z * SR)]
    n = (len(s) - NF) // HOP
    if n < 20:
        return None
    fr = np.stack([s[i * HOP: i * HOP + NF] * WIN for i in range(n)])
    lm = np.log((np.abs(np.fft.rfft(fr)) ** 2) @ FB.T + 1e-8)
    e = lm.sum(1)
    lm = lm[e > np.percentile(e, 40)]  # trames parlées
    return np.r_[lm.mean(0), lm.std(0)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("media")
    ap.add_argument("refs")
    ap.add_argument("intervalles")
    args = ap.parse_args()
    utf8()
    x = decode(args.media, SR)
    refs = json.loads(Path(args.refs).read_text(encoding="utf-8-sig"))
    ref = {k: np.mean([empreinte(x, a, z) for a, z in v], axis=0) for k, v in refs.items()}
    mu, sd = np.mean(list(ref.values()), 0), np.std(list(ref.values()), 0) + 1e-6
    Z = lambda f: (f - mu) / sd

    def qui(a, z):
        f = empreinte(x, a, z)
        if f is None:
            return "?", 0.0
        s = {k: float(np.dot(Z(f), Z(r)) / (np.linalg.norm(Z(f)) * np.linalg.norm(Z(r)))) for k, r in ref.items()}
        b = max(s, key=s.get)
        return b, s[b]

    iv = json.loads(Path(args.intervalles).read_text(encoding="utf-8-sig"))
    groupes = iv if isinstance(iv, dict) else {"intervalles": iv}
    for nom, lst in groupes.items():
        print("==", nom)
        for i, it in enumerate(lst):
            a, z = (it["start"], it["end"]) if isinstance(it, dict) else it
            b, c = qui(a, z)
            print(f"  #{i} {a:.1f}-{z:.1f} ({z - a:.1f} s) : {b} {c:.2f}{'  (peu fiable)' if c < 0.3 else ''}")


if __name__ == "__main__":
    main()
