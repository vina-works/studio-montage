"""Repère les plans (changements de caméra) dans des intervalles et produit une planche pour choisir le cadrage vertical.

Usage : python planche_plans.py source.mp4 intervalles.json -o plans.json
  intervalles.json : {"nom": [[début, fin], ...]}  (temps de la source)
Sortie : plans.json ({"nom": [{"start", "end"}]}) et une planche planche_<nom>.jpg par entrée :
une image au milieu de chaque plan, numérotée, graduée tous les 240 px (repères 2, 4, 7, 9... = x/100).
On y lit la position du visage pour remplir cadrage.json (voir wiki/07-shorts.md).
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

from commun import ffmpeg, utf8

FONT = "C\\:/Windows/Fonts/arialbd.ttf"


def main():
    utf8()
    ap = argparse.ArgumentParser()
    ap.add_argument("source")
    ap.add_argument("intervalles")
    ap.add_argument("-o", "--sortie", default="plans.json")
    args = ap.parse_args()
    iv = json.loads(Path(args.intervalles).read_text(encoding="utf-8-sig"))
    out_dir = Path(args.sortie).parent
    tout = {}
    for nom, lst in iv.items():
        plans = []
        for a, z in lst:
            r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-ss", str(a), "-t", str(z - a), "-i", args.source, "-an", "-vf", "select='gt(scene,0.2)',showinfo", "-f", "null", "-"],
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            b = [a] + [a + float(x) for x in re.findall(r"pts_time:([\d.]+)", r.stderr)] + [z]
            plans += [{"start": round(x, 3), "end": round(y, 3)} for x, y in zip(b, b[1:]) if y - x >= 0.1]
        tout[nom] = plans
        vign = []
        for i, p in enumerate(plans):
            f = out_dir / f".vign_{i}.jpg"
            ticks = ",".join(f"drawbox=x={x}:y=0:w=2:h=10:color=yellow:t=fill,drawtext=fontfile='{FONT}':text='{x * 5 // 100}':x={x + 2}:y=10:fontsize=11:fontcolor=yellow" for x in range(0, 384, 48))
            ffmpeg("-ss", f"{(p['start'] + p['end']) / 2:.2f}", "-i", args.source, "-frames:v", 1,
                   "-vf", f"scale=384:216,{ticks},drawbox=x=0:y=196:w=110:h=20:color=black:t=fill,drawtext=fontfile='{FONT}':text='#{i} {p['end'] - p['start']:.1f}s':x=3:y=200:fontsize=13:fontcolor=white", f)
            vign.append(f)
        cols = 5
        n = len(vign)
        lay = "|".join(f"{(i % cols) * 384}_{(i // cols) * 216}" for i in range(n))
        ins = [x for f in vign for x in ("-i", f)]
        filt = f"xstack=inputs={n}:layout={lay}:fill=black" if n > 1 else "null"
        ffmpeg(*ins, "-filter_complex", filt, "-q:v", 3, out_dir / f"planche_{nom}.jpg")
        for f in vign:
            f.unlink()
        print(nom, len(plans), "plans")
    Path(args.sortie).write_text(json.dumps(tout, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
