"""Shorts verticaux 1080x1920 : cadrage plan par plan, sous-titres mot à mot, accroche 3 s, bandeau de fin.

Usage : python shorts.py shorts.json [--seul 4_vous_priez] -o rendus/shorts
  shorts.json  : source, offset, podcast, transcription, cadrage, et pour chaque short ses extraits
                 (temps de la transcription), son accroche, la liste de plans à utiliser.
  cadrage.json : {"liste": [{"start", "end", "x", "y", "largeur"}]} en temps et pixels de la source 1920x1080 ;
                 x, y = centre du visage ; largeur = 500 gros plan, 405 plan moyen, 360 plan large.
Voir wiki/07-shorts.md et theme/README.md.
"""
import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

import numpy as np

from commun import FILL, couleur_ass, decode, ffmpeg, glossaire, mots, noms_propres, norm, t, theme, utf8

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
SR, FPS = 48000, 30
R = {"marge": 0.12, "pause": 0.32, "seuil": 0.5}
PROPRES = noms_propres()
TH = theme()
C, P = TH["couleurs"], TH["polices"]
FONTS = f'<link href="{P["url"]}" rel=stylesheet>'
CADRE = (f"position:absolute;left:60px;right:60px;top:130px;background:{C['fond']};border-left:12px solid {C['accent']};padding:30px 38px;"
         f"font-family:'{P['titre']}',sans-serif;font-weight:{P['titre_graisse']};font-size:58px;line-height:1.14;color:{C['texte']}")


def page(work, nom, texte):
    f = work / f"{nom}.html"
    f.write_text(f"<!doctype html><meta charset=utf-8>{FONTS}<style>*{{margin:0}}html,body{{width:1080px;height:1920px;background:transparent}}</style>"
                 f"<div style=\"{CADRE}\">{texte.replace(' ?', '&nbsp;?')}</div>", encoding="utf-8")
    p = work / f"{nom}.png"
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--window-size=1080,1920", "--virtual-time-budget=6000",
                    "--default-background-color=00000000", f"--screenshot={p}", f.as_uri()], capture_output=True, timeout=120)
    return p


def morceaux(W, a, z, s0, z0):
    ws = [w for w in W if a - 0.05 <= w["start"] < z - 0.05 and norm(w["w"]) not in FILL]
    parts = [[ws[0]["start"] - R["marge"], ws[0]["end"]]]
    for p, q in zip(ws, ws[1:]):
        if q["start"] - p["end"] > R["seuil"]:
            parts[-1][1] = p["end"] + R["pause"] / 2
            parts.append([q["start"] - R["pause"] / 2, q["end"]])
        else:
            parts[-1][1] = q["end"]
    parts[-1][1] += R["marge"]
    parts[0][0] = s0 if s0 is not None else parts[0][0]
    parts[-1][1] = z0 if z0 is not None else parts[-1][1]
    return parts, ws


def ass(work, key, words, dur, cuts, regles):
    disp = []
    for w in words:  # « 'est », « -ce », « ? » se recollent au mot précédent
        tok = w["w"]
        if disp and tok[:1] in "'-?%!":
            disp[-1]["w"] += ("\u00a0" if tok[:1] in "?%!" else "") + tok
            disp[-1]["z"] = w["z"]
        else:
            disp.append(dict(w))
    for d in disp:
        if d["w"][:1].isupper() and d["w"].strip(",.?") not in PROPRES:
            d["w"] = d["w"][0].lower() + d["w"][1:]
        for a, b in regles:
            d["w"] = re.sub(a, b, d["w"])
    groups, cur = [], []
    for d in disp:
        coupe = any(cur and cur[-1]["z"] <= b + 0.02 and d["a"] >= b - 0.02 for b in cuts)
        if cur and (coupe or len(cur) >= 4 or len(" ".join(x["w"] for x in cur + [d])) > 20 or d["a"] - cur[-1]["z"] > 0.3):
            groups.append(cur)
            cur = []
        cur.append(d)
    if cur:
        groups.append(cur)

    def ts(x):
        h, r = divmod(x, 3600)
        m, s = divmod(r, 60)
        return f"{int(h)}:{int(m):02d}:{s:05.2f}"

    ev = []
    for gi, g in enumerate(groups):
        ge = groups[gi + 1][0]["a"] if gi + 1 < len(groups) else dur
        for i, d in enumerate(g):
            e = g[i + 1]["a"] if i + 1 < len(g) else min(ge, d["z"] + 0.4)
            txt = " ".join(("{\\c&H" + couleur_ass(C["accent"]) + "&}" + x["w"] + "{\\c&H" + couleur_ass(C["texte"]) + "&}")
                           if j == i else x["w"] for j, x in enumerate(g))
            ev.append(f"Dialogue: 0,{ts(d['a'])},{ts(max(e, d['a'] + 0.05))},S,,0,0,0,,{txt}")
    head = ("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 2\n\n[V4+ Styles]\n"
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            f"Style: S,Segoe UI Black,104,&H00{couleur_ass(C['texte'])},&H00{couleur_ass(C['texte'])},&H00{couleur_ass(C['fond'])},&H00000000,0,0,0,0,100,100,0,0,1,7,0,2,50,50,500,1\n\n[Events]\n"
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    f = work / f"{key}.ass"
    f.write_text(head + "\n".join(ev) + "\n", encoding="utf-8")
    return f.name


def main():
    utf8()
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("-o", "--sortie", required=True)
    ap.add_argument("--seul", nargs="*")
    args = ap.parse_args()
    base = Path(args.spec).parent
    spec = json.loads(Path(args.spec).read_text(encoding="utf-8-sig"))
    cad = json.loads((base / spec["cadrage"]).read_text(encoding="utf-8-sig"))
    W, _ = mots(spec["transcription"])
    off, src, regles = spec.get("offset", 0.0), spec["source"], glossaire()
    out_dir = Path(args.sortie)
    out_dir.mkdir(parents=True, exist_ok=True)
    work = out_dir / ".travail"
    work.mkdir(exist_ok=True)
    x = decode(src, SR, 2)
    bandeau = page(work, "bandeau", spec["bandeau_fin"])
    for key, s in spec["shorts"].items():
        if args.seul and key not in args.seul:
            continue
        keep, words, T = [], [], 0.0
        for e in s["extraits"]:
            parts, ws = morceaux(W, t(e["debut"]), t(e["fin"]), t(e.get("debut_force")), t(e.get("fin_force")))
            for p in parts:
                A, Z = round((p[0] + off) * FPS) / FPS, round((p[1] + off) * FPS) / FPS
                keep.append({"start": A, "end": Z, "out": T})
                for w in ws:
                    m = (w["start"] + w["end"]) / 2 + off
                    if A <= m < Z:
                        words.append({"w": w["w"], "a": T + max(0, w["start"] + off - A), "z": T + min(Z - A, w["end"] + off - A)})
                T += Z - A
        plans = cad[s["plans"]]
        seg = work / key
        shutil.rmtree(seg, ignore_errors=True)
        seg.mkdir()
        lines, done, acc, n = [], 0, 0.0, 0
        for k in keep:
            hit = [(p, max(k["start"], p["start"]), min(k["end"], p["end"])) for p in plans if min(k["end"], p["end"]) - max(k["start"], p["start"]) >= 0.02]
            if not hit:  # passage absent des plans repérés : on prend le plus proche
                p = min(plans, key=lambda p: min(abs(p["start"] - k["end"]), abs(p["end"] - k["start"])))
                hit = [(p, k["start"], k["end"])]
            hit = [(p, hit[j - 1][2] if j else k["start"], k["end"] if j == len(hit) - 1 else z) for j, (p, a, z) in enumerate(hit)]
            for p, a, z in hit:
                acc += z - a
                frames = round(acc * FPS) - done
                if frames <= 0:
                    continue
                done += frames
                h = round(p["largeur"] * 16 / 9)
                h -= h % 2
                w2 = round(h * 9 / 16)
                cx, top = max(0, min(1920 - w2, p["x"] - w2 // 2)), max(0, min(1080 - h, p["y"] - round(h * 0.33)))
                f = seg / f"{n:03d}.mp4"
                n += 1
                ffmpeg("-ss", f"{a:.3f}", "-i", src, "-an", "-frames:v", frames, "-r", FPS, "-vf", f"crop={w2}:{h}:{cx}:{top},scale=1080:1920:flags=lanczos,setsar=1",
                       "-c:v", "libx264", "-preset", "ultrafast", "-crf", 12, "-pix_fmt", "yuv420p", f)
                lines.append(f"file '{f.as_posix()}'")
        (seg / "list.txt").write_text("\n".join(lines), encoding="utf-8")
        nfade, parts = int(0.02 * SR), []
        for k in keep:
            a = x[int(k["start"] * SR): int(k["end"] * SR)].copy()
            m = min(nfade, len(a) // 2)
            r = np.linspace(0, 1, m, dtype=np.float32)[:, None]
            a[:m] *= r
            a[-m:] *= r[::-1]
            parts.append(a)
        (seg / "a.raw").write_bytes(np.concatenate(parts).tobytes())
        dur = done / FPS
        hook = page(work, f"accroche_{key}", s["accroche"])
        a_name = ass(work, key, words, dur, [k["out"] for k in keep], regles)
        st = max(3.2, dur - 1.8)
        fc = (f"[0:v]ass={a_name}[s];[2:v]format=rgba,fade=t=out:st=2.75:d=0.25:alpha=1[h];[s][h]overlay=0:0:enable='lt(t,3)'[a];"
              f"[a][3:v]overlay=0:0:enable='gte(t,{st:.2f})'[v]")
        o = out_dir / f"short_{key}.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(seg / "list.txt"), "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", str(seg / "a.raw"),
                        "-loop", "1", "-framerate", str(FPS), "-t", "3.2", "-i", str(hook), "-loop", "1", "-framerate", str(FPS), "-i", str(bandeau),
                        "-filter_complex", fc, "-map", "[v]", "-map", "1:a", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", f"{dur:.3f}", str(o)], check=True, cwd=work)  # -t et non -shortest
        shutil.rmtree(seg)
        print(key, f"{dur:.1f} s", flush=True)
    shutil.rmtree(work)


if __name__ == "__main__":
    main()
