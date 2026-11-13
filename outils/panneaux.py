"""Panneaux d'illustration mi-écran (960x1080) aux couleurs du thème, rendus par Chrome sans interface.

Usage : python panneaux.py panneaux.json [--video preecoute.mp4] [--seul 07_contexte]
  - écrit <id>.html et <id>.png à côté de panneaux.json ;
  - avec --video, ajoute <id>_incrust.jpg (moitié gauche de la vidéo au `moment`, panneau à droite)
    et une planche.jpg, pour vérifier placement et lisibilité.
Le champ `moment` est un temps de sortie du montage ; `rendu.py --panneaux` s'en sert.
Voir wiki/05-illustrations-mi-ecran.md et wiki/README.md.
"""
import argparse
import json
import subprocess
from pathlib import Path

from commun import ffmpeg, utf8

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
FONTS = ("https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Inter:wght@600"
         "&family=Noto+Sans+Arabic&family=Noto+Sans+Canadian+Aboriginal&family=Noto+Sans+Symbols+2&family=Noto+Sans&display=block")
CSS = """*{box-sizing:border-box;margin:0}
html,body{width:960px;height:1080px;background:#1c1d21;color:#f2f2f2;font-family:'JetBrains Mono','Noto Sans Arabic','Noto Sans Canadian Aboriginal','Noto Sans Symbols 2','Noto Sans',monospace;overflow:hidden}
.p{position:absolute;inset:0;padding:96px 72px 72px;display:flex;flex-direction:column;border-left:4px solid #3b82f6}
.k{font-size:30px;color:#b4b6bd}
h1{font-family:'Inter',sans-serif;font-weight:600;font-size:76px;line-height:1.06;margin:18px 0 22px;letter-spacing:-1px}
.s{font-size:36px;line-height:1.42}
.v{flex:1;display:flex;flex-direction:column;justify-content:center;gap:24px;min-height:0}
.foot{display:flex;justify-content:space-between;align-items:flex-end;font-size:26px;color:#8a8c94;gap:24px}
.fox{font-size:42px;white-space:nowrap}.fox b,.r{color:#3b82f6;font-weight:600}
.box{background:#15161a;border:2px solid #34353c;border-radius:14px;padding:28px;font-size:33px;line-height:1.4}
.box.on{border-color:#3b82f6}.t{font-size:25px;color:#8a8c94;margin-bottom:10px}
.row{display:flex;gap:22px;align-items:stretch}.row>*{flex:1}
.big{font-family:'Inter',sans-serif;font-weight:600;font-size:46px}
.arrow{flex:0 0 auto!important;align-self:center;font-size:44px;color:#8a8c94}
.btn{display:inline-block;background:#f2f2f2;color:#1c1d21;border-radius:10px;padding:14px 22px;font-weight:600;font-size:30px}
.bar{height:46px;border-radius:10px;background:#15161a;border:2px solid #34353c;overflow:hidden}.bar i{display:block;height:100%;background:#f2f2f2}.bar i.red{background:#3b82f6}
.u{color:#b4b6bd;font-size:31px;padding:7px 0}"""
RENARDS = {"content": ""}


def html(p):
    fox = RENARDS.get(p.get("renard", "content"), p.get("renard", ""))
    return (f"<!doctype html><meta charset=utf-8><link href=\"{FONTS}\" rel=stylesheet><style>{CSS}</style>"
            f"<div class=p><div class=k>// {p['surtitre']}</div><h1>{p['titre']}</h1><div class=s>{p['texte']}</div>"
            f"<div class=v>{p.get('visuel', '')}</div><div class=foot><span>{p.get('pied', '')}</span><span class=fox>{fox}</span></div></div>")


def main():
    utf8()
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--video")
    ap.add_argument("--seul")
    args = ap.parse_args()
    d = Path(args.spec).parent
    spec = json.loads(Path(args.spec).read_text(encoding="utf-8-sig"))
    faits = []
    for p in spec["panneaux"]:
        if args.seul and p["id"] != args.seul:
            continue
        h = d / f"{p['id']}.html"
        h.write_text(html(p), encoding="utf-8")
        png = d / p.get("png", f"{p['id']}.png")
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--window-size=960,1080", "--virtual-time-budget=6000",
                        f"--screenshot={png}", h.as_uri()], capture_output=True, timeout=120)
        if args.video and p.get("moment") is not None:
            jpg = d / f"{p['id']}_incrust.jpg"
            ffmpeg("-ss", f"{p['moment'] + 1:.2f}", "-i", args.video, "-i", png, "-frames:v", "1",
                   "-filter_complex", "[0:v]scale=1920:1080,crop=960:1080:480:0[l];[1:v]scale=960:1080[r];[l][r]hstack", "-q:v", 3, jpg)
            faits.append(jpg)
        print(p["id"], "OK" if png.exists() else "ÉCHEC")
    if len(faits) > 1:
        args_in = [x for f in faits for x in ("-i", f)]
        n = len(faits)
        lay = "|".join(f"{(i % 2) * 768}_{(i // 2) * 432}" for i in range(n))
        fc = "".join(f"[{i}:v]scale=768:-1[v{i}];" for i in range(n)) + "".join(f"[v{i}]" for i in range(n)) + f"xstack=inputs={n}:layout={lay}"
        ffmpeg(*args_in, "-filter_complex", fc, "-q:v", 3, d / "planche.jpg")


if __name__ == "__main__":
    main()
