"""Mesure le décalage entre deux versions d'un même enregistrement (ex. MP3 transcrit et MP4 habillé).

Usage : python aligner.py reference.mp3 cible.mp4 [--pas 30]
Pour chaque fenêtre de 4 s de la référence, cherche où elle tombe dans la cible. Affiche les
zones de décalage constant et celles qui n'existent pas dans la cible (corrélation faible).
"""
import argparse

import numpy as np

from commun import decode, utf8

SR = 2000  # assez pour la voix, et la FFT reste rapide


def main():
    utf8()
    ap = argparse.ArgumentParser()
    ap.add_argument("reference")
    ap.add_argument("cible")
    ap.add_argument("--pas", type=float, default=30)
    args = ap.parse_args()
    a, v = decode(args.reference, SR), decode(args.cible, SR)
    print(f"durées : référence {len(a) / SR:.1f} s, cible {len(v) / SR:.1f} s")
    N = 1 << int(np.ceil(np.log2(len(v) + 4 * SR)))  # taille fixe en puissance de 2 : sinon la FFT peut prendre des minutes
    V = np.fft.rfft(v, N)
    prev, offs = None, []
    for t0 in np.arange(5, len(a) / SR - 5, args.pas):
        w = a[int(t0 * SR): int((t0 + 4) * SR)]
        w = w - w.mean()
        c = np.fft.irfft(V * np.conj(np.fft.rfft(w, N)))[: len(v)]
        i = int(np.argmax(np.abs(c)))
        q = abs(c[i]) / (np.sqrt(np.sum(w ** 2) * np.sum(v[i:i + len(w)] ** 2)) + 1e-9)
        off = i / SR - t0
        if q < 0.6:
            print(f"{t0:8.1f} s : absent de la cible (corrélation {q:.2f})")
            prev = None
        elif prev is None or abs(off - prev) > 0.02:
            print(f"{t0:8.1f} s : décalage {off:+.3f} s (corrélation {q:.2f})")
            prev = off
        if q >= 0.6:
            offs.append(off)
    if offs:
        print(f"décalage médian : {np.median(offs):+.3f} s (précision ±{1 / SR:.4f} s ; affiner localement si besoin)")


if __name__ == "__main__":
    main()
