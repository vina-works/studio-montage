"""edit.json -> vidéo montée. Image coupée à l'image près, son au sample près, fondu de 20 ms à chaque raccord.

Usage :
  python rendu.py edit.json -o rendus/episode.mp4                    rendu final 1080p (libx264 veryfast crf 20, AAC 192k)
  python rendu.py edit.json -o tmp/preecoute.mp4 --apercu            préécoute 720p (NVENC)
  python rendu.py edit.json -o ... --panneaux panneaux.json          avec les illustrations mi-écran
  python rendu.py edit.json -o tmp/preecoute.m4a --audio             son seul

Le fichier de sortie n'est jamais écrasé. Voir wiki/04-source-video-synchro-rendu.md.
"""
import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

from commun import decode, ffmpeg, utf8

FPS, SR = 30, 48000


def audio_monte(edit, sortie_raw):
    x = decode(edit["source"], SR, 2)
    n = int(0.02 * SR)
    parts = []
    for k in edit["keep"]:
        p = x[int(k["start"] * SR): int(k["end"] * SR)].copy()
        m = min(n, len(p) // 2)
        r = np.linspace(0, 1, m, dtype=np.float32)[:, None]
        p[:m] *= r
        p[-m:] *= r[::-1]
        parts.append(p)
    y = np.concatenate(parts)
    Path(sortie_raw).write_bytes(y.tobytes())
    return len(y) / SR


def main():
    utf8()
    ap = argparse.ArgumentParser()
    ap.add_argument("edit")
    ap.add_argument("-o", "--sortie", required=True)
    ap.add_argument("--apercu", action="store_true")
    ap.add_argument("--audio", action="store_true")
    ap.add_argument("--panneaux")
    args = ap.parse_args()
    out = Path(args.sortie)
    if out.exists():
        sys.exit(f"Existe déjà, rien n'est écrasé : {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    edit = json.loads(Path(args.edit).read_text(encoding="utf-8-sig"))
    work = out.parent / f".travail_{out.stem}"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    dur = audio_monte(edit, work / "a.raw")
    raw = ["-f", "f32le", "-ar", SR, "-ac", 2, "-i", work / "a.raw"]
    if args.audio:
        ffmpeg(*raw, "-c:a", "aac", "-b:a", "192k", out)
        shutil.rmtree(work)
        print("OK", out, f"{dur:.2f} s")
        return
    W, H = (1280, 720) if args.apercu else (1920, 1080)
    lines, done, acc = [], 0, 0.0
    for i, k in enumerate(edit["keep"]):
        acc += k["end"] - k["start"]
        frames = round(acc * FPS) - done  # arrondi cumulé : les erreurs ne s'additionnent pas
        if frames <= 0:
            continue
        done += frames
        f = work / f"{i:04d}.mp4"
        enc = ["-c:v", "h264_nvenc", "-preset", "p3", "-cq", "26"] if args.apercu else ["-c:v", "libx264", "-preset", "ultrafast", "-crf", "10"]
        ffmpeg("-ss", f"{k['start']:.3f}", "-i", edit["source"], "-an", "-frames:v", frames, "-r", FPS, "-vf", f"scale={W}:{H},setsar=1", *enc, "-pix_fmt", "yuv420p", f)
        lines.append(f"file '{f.as_posix()}'")
        if i % 20 == 0:
            print(f"segment {i}/{len(edit['keep'])}", flush=True)
    (work / "list.txt").write_text("\n".join(lines), encoding="utf-8")
    args_ff = ["-f", "concat", "-safe", 0, "-i", work / "list.txt", *raw]
    fc, maps = None, ["-map", "0:v"]
    if args.panneaux:  # vidéo recentrée à gauche, panneau glissé à droite
        spec = json.loads(Path(args.panneaux).read_text(encoding="utf-8-sig"))
        base = Path(args.panneaux).parent
        P = [(base / p["png"], p["moment"], p["duree"]) for p in spec["panneaux"] if p.get("moment") is not None]
        for png, _, _ in P:
            args_ff += ["-framerate", FPS, "-loop", 1, "-i", png]
        on = "+".join(f"between(t,{m},{m + d})" for _, m, d in P)
        half = W // 2
        fc = f"[0:v]split[m][c];[c]crop={half}:{H}:{W // 4}:0[l];[m][l]overlay=0:0:enable='{on}'[b0];"
        S = 0.3
        for i, (_, m, d) in enumerate(P):
            e = m + d
            x = f"if(lt(t,{m + S}),{W}-{half}*(t-{m})/{S},if(gt(t,{e - S}),{half}+{half}*(t-{e - S})/{S},{half}))"
            fc += f"[{i + 2}:v]scale={half}:{H}[p{i}];[b{i}][p{i}]overlay=x='{x}':y=0:eof_action=pass:enable='between(t,{m},{e})'[b{i + 1}];"
        fc, maps = fc.rstrip(";"), ["-map", f"[b{len(P)}]"]
    venc = ["-c:v", "h264_nvenc", "-preset", "p3", "-cq", "26"] if args.apercu else ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20"]
    ffmpeg(*args_ff, *(["-filter_complex", fc] if fc else []), *maps, "-map", "1:a", *venc, "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", f"{done / FPS:.3f}", out)
    shutil.rmtree(work)
    pistes = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,duration", "-of", "csv=p=0", str(out)], capture_output=True, text=True).stdout.split()
    print("OK", out, "attendu", f"{done / FPS:.3f} s", "pistes", " ".join(pistes))


if __name__ == "__main__":
    main()
