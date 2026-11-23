/* Montage : timeline éditable de la salle de revue.
 *
 * Charge un plan de coupe (edit*.json à la racine du dossier de travail, plusieurs sources), ses
 * cartes (<nom>.overlays.json) et les repères de la salle (commentaires, moments forts), les affiche
 * sur une timeline, et enregistre les retouches dans revue/montage/<nom>.manuel.json.
 * L'aperçu rejoue les plans depuis les prises d'origine, avec les cartes animées, l'encadré pendant les
 * captures, les sous-titres recalculés et un fondu de 20 ms aux raccords, comme le rendu.
 * Les fonctions $, uid, notif, esc, stock et les variables etat, video viennent de index.html.
 */
(() => {
'use strict';
const q = s => document.querySelector(s);
const FPS = 60;
const MT = window.MT = { actif: false };
const COUL = ['#5a52e0', '#2b86c9', '#b0527a', '#3f9a6d'];
const CATS = { fort: ['Moment fort', '#ffb020'], short: ['Idée de short', '#b06cff'], citation: ['Citation', '#3ea8ff'], rire: ['Rire', '#2fd27a'], couper: ['À couper', '#ff4d5e'] };
let M = null, drag = null, tSave = null;
let sauvegarde = Promise.resolve();
const VITESSES_MT = [1, 1.5, 2, 3];
let vitesseMt = VITESSES_MT.includes(+stock.get('mtVitesse', 1)) ? +stock.get('mtVitesse', 1) : 1;

const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const fmt = s => { s = Math.max(0, s || 0); const m = Math.floor(s / 60), r = s - m * 60; return m + ':' + r.toFixed(2).padStart(5, '0'); };
const strip = c => ({ id: c.id, src: c.src, a: +c.a.toFixed(3), b: +c.b.toFixed(3), why: c.why || '' });
const dureeSrc = src => (etat.assets.find(a => a.chemin === src)?.duree) || 1e9;
const court = s => String(s || '').replace(/^.*[\\/]/, '').replace(/^2026-11-19 /, '').replace('.mp4', '');
const TYPES_VISUEL = { P: 'Carte', S: 'Capture', T: 'Bandeau' };
const MODES_VISUEL = {
  P: { side: 'À côté de la vidéo', full: 'Plein écran' },
  S: { pip: 'Avec l’intervenant en vignette', full: 'Plein écran' },
  T: { lower: 'En bas à gauche', right: 'En bas à droite', side: 'À côté de la vidéo' },
};
const modeVisuel = o => o.mode || Object.keys(MODES_VISUEL[o.kind] || {})[0];
const nomVisuel = o => o.label || o.id;

/* ---------- données ---------- */
function layout() { let o = 0; for (const c of M.clips) { c.o = o; c.d = c.b - c.a; o += c.d; } M.total = o; }
function toSrc(T) {
  const cl = M.clips;
  for (let i = 0; i < cl.length; i++) if (T >= cl[i].o && T < cl[i].o + cl[i].d) return { clip: cl[i], i };
  return cl.length ? { clip: cl[cl.length - 1], i: cl.length - 1 } : null;
}
function toOut(src, t) {
  const cl = M.clips;
  for (let i = 0; i < cl.length; i++) {
    const c = cl[i];
    if (c.src === src && t >= c.a - 0.2 && t < c.b) return c.o + Math.max(0, t - c.a);
    if (c.src === src && t < c.a) { const p = cl[i - 1]; if (!p || p.src !== src || t >= p.b) return c.o; }
  }
  return null;
}
function toOutStrict(src, t) {
  for (const c of M.clips) if (c.src === src && t >= c.a && t < c.b) return c.o + (t - c.a);
  return null;
}
function ovTemps(ov) { const S = toOut(ov.src, ov.at); return S == null ? null : { S, E: Math.min(S + ov.d, M.total) }; }
function motsDe(src) { return M.mots[src] || []; }
function corrigerMots() {
  M.motsCorriges = Object.fromEntries(Object.entries(M.mots).map(([src, ws]) => [src, ws.slice()]));
  for (const { source, index, original, start, end, texte } of M.corrections) {
    const mot = M.mots[source]?.[index];
    if (mot?.[0] === original && mot[1] === start && mot[2] === end) {
      M.motsCorriges[source][index] = [texte, start, end];
    }
  }
}
function texteClip(c) {
  const ws = M.motsCorriges[c.src] || [];
  return nettoyerTexte(ws.filter(([, s]) => s >= c.a - 0.01 && s < c.b).map(([w]) => w).filter(Boolean).join(' '));
}
function aimanter(src, t, mode) {
  if (!M.aimant) return Math.round(t * FPS) / FPS;
  const ws = motsDe(src); let best = null, bd = 0.25;
  for (const [, s, e] of ws) {
    const v = mode === 'start' ? s - 0.12 : e + 0.12, d = Math.abs(v - t);
    if (d < bd) { bd = d; best = v; }
  }
  return best ?? Math.round(t * FPS) / FPS;
}

/* sous-titres : même découpe et mêmes corrections que le rendu */
const CORRECTIONS = [[/\bCloudCode\b/g, 'Claude Code'], [/\bcloud code\b/g, 'Claude Code'], [/\bwrite-coder\b/g, 'vibe-coder'], [/\bwrite-code\b/g, 'vibe-code']];
function nettoyerTexte(t) {
  for (const [a, b] of CORRECTIONS) t = t.replace(a, b);
  t = t.replace(/\s+([,.;:!?…])/gu, '$1').replace(/(\p{L})\s'/gu, "$1'").replace(/(\p{L})\s?'\s?(\p{L})/gu, "$1'$2").replace(/\s*-\s*(\p{L})/gu, '-$1');
  return t;
}
function calculerSousTitres() {
  const cues = [];
  for (const c of M.clips) {
    const ws = (M.motsCorriges[c.src] || []).filter(([w, s]) => w && s >= c.a - 0.001 && s < c.b - 0.03);
    let cur = [];
    const vider = () => {
      if (!cur.length) return;
      const texte = nettoyerTexte(cur.map(w => w[0]).join(' '));
      const a = clamp(c.o + cur[0][1] - c.a, c.o, c.o + c.d);
      const b = Math.min(c.o + cur[cur.length - 1][2] - c.a + 0.1, c.o + c.d, a + 0.5 + 0.07 * texte.length);
      cues.push({ a, b: Math.max(b, a + 0.3), texte }); cur = [];
    };
    for (const w of ws) {
      const txt = cur.map(x => x[0]).join(' '), der = cur.length ? cur[cur.length - 1][0].slice(-1) : '';
      if (cur.length && (txt.length + w[0].length > 80 || w[1] - cur[cur.length - 1][2] > 0.6 || (txt.length > 22 && '.?!'.includes(der)) || (txt.length > 48 && ',;:'.includes(der)))) vider();
      cur.push(w);
    }
    vider();
  }
  for (let i = 0; i + 1 < cues.length; i++) if (cues[i].b > cues[i + 1].a) cues[i].b = cues[i + 1].a - 0.01;
  M.cues = cues;
}

/* repères : commentaires et moments de la salle (lecture seule) + repères posés ici */
function tousRepères() {
  const out = [];
  for (const r of M.rep) {
    if (!M.filtres[r.type === 'moment' ? 'moments' : 'comms']) continue;
    const strict = toOutStrict(r.src, r.at), S = strict ?? toOut(r.src, r.at);
    if (S == null) continue;
    let E = null;
    if (r.at_fin != null && strict != null) { const e = toOutStrict(r.src, r.at_fin - 0.001); if (e != null && e > S) E = e; }
    out.push({ ...r, k: 'room:' + r.media + ':' + r.id, S, E, dehors: strict == null });
  }
  if (M.filtres.marks) for (const m of M.marks) {
    const strict = toOutStrict(m.src, m.at), S = strict ?? toOut(m.src, m.at);
    if (S == null) continue;
    out.push({ ...m, k: 'mark:' + m.id, type: 'repère', texte: m.label, S, E: null, dehors: strict == null });
  }
  return out.sort((a, b) => a.S - b.S);
}
const couleurRep = r => r.type === 'moment' ? (CATS[r.cat] || CATS.fort)[1] : r.type === 'repère' ? '#3ea8ff' : (r.resolu ? '#6d6e78' : '#f5f5f5');

/* historique */
const instantane = () => JSON.stringify({ c: M.clips.map(strip), o: M.overlays, k: M.marks, texte: M.corrections });
function snapshot() { M.hist.push(instantane()); if (M.hist.length > 120) M.hist.shift(); M.fut = []; }
function restaurer(json) {
  const d = JSON.parse(json);
  M.clips = d.c.map(c => ({ ...c })); M.overlays = d.o.map(o => ({ ...o })); M.marks = (d.k || []).map(m => ({ ...m })); M.corrections = d.texte;
  M.sel = null; M.selOv = null; M.selRep = null; rendre(); planifier();
}
function annuler() { if (!M.hist.length) return notif('Rien à annuler'); M.fut.push(instantane()); restaurer(M.hist.pop()); notif('Annulé'); }
function retablir() { if (!M.fut.length) return notif('Rien à rétablir'); M.hist.push(instantane()); restaurer(M.fut.pop()); notif('Rétabli'); }

/* ---------- chargement ---------- */
async function charger() {
  const liste = await (await fetch('/api/montages')).json();
  if (!liste.length) { notif('Aucun plan de coupe (edit*.json) à la racine du dossier de travail'); return false; }
  const f = liste[0];
  const d = await (await fetch('/api/montage?p=' + encodeURIComponent(f))).json();
  const base = d.manuel || null;
  M = {
    f, edit: d.edit, images: new Map(), sources: d.edit.sources || [...new Set(d.edit.keep.map(k => k.source))],
    clips: (base?.keep || d.edit.keep).map(k => ({ id: uid(), src: k.source, a: k.start, b: k.end, why: k.why || '' })),
    overlays: (base?.overlays || d.overlays || []).map(o => ({ ...o })),
    corrections: base?.corrections_transcript || d.edit.corrections_transcript || [],
    marks: (base?.reperes || []).map(m => ({ ...m })), rep: d.reperes || [],
    filtres: { comms: true, moments: true, marks: true }, onglet: 'edition',
    mots: {}, vids: {}, sel: null, selOv: null, selRep: null, pxs: stock.get('mt.pxs', 4), t: 0, playing: false,
    aimant: stock.get('mt.aimant', true), sousTitres: stock.get('mt.st', true), cues: [], hist: [], fut: [], cur: null, original: { keep: d.edit.keep, overlays: d.overlays || [] },
    manuelCharge: !!base,
  };
  await Promise.all(M.sources.map(async s => { M.mots[s] = await (await fetch('/api/transcript?p=' + encodeURIComponent(s))).json().catch(() => []); }));
  construireScene();
  layout(); rendre(); allerA(0);
  return true;
}
function construireScene() {
  const sc = q('#mtScene'); sc.innerHTML = '';
  sc.classList.toggle('wide', M.edit.habillage === true);
  q('#mtAddVisuel').hidden = !M.edit.habillage;
  const image = M.edit.habillage ? document.createElement('div') : sc;
  if (image !== sc) {
    image.className = 'mt-video-frame';
    sc.appendChild(image);
  }
  M.sources.forEach(s => {
    const v = document.createElement('video'); v.preload = 'auto'; v.playsInline = true;
    v.src = '/media?p=' + encodeURIComponent(s); v.style.display = 'none';
    v.preservesPitch = true;
    v.addEventListener('loadedmetadata', () => { v.playbackRate = vitesseMt; });
    image.appendChild(v); M.vids[s] = v;
  });
  sc.insertAdjacentHTML('beforeend', '<div class="mt-st" id="mtSt"></div><div class="mt-badge">Aperçu du montage</div>');
}

function synchroniserVisuels() {
  const actifs = new Set(M.overlays.map(o => o.id));
  for (const [id, im] of M.images) {
    if (!actifs.has(id)) { im.remove(); M.images.delete(id); }
  }
  for (const o of M.overlays) {
    let im = M.images.get(o.id);
    if (!im) {
      im = document.createElement('img'); im.alt = ''; im.dataset.ov = o.id;
      q('#mtScene').appendChild(im); M.images.set(o.id, im);
    }
    const src = /^data:image\/(png|jpeg|webp);base64,[A-Za-z0-9+/=]+$/.test(o.img)
      ? o.img : '/img?p=' + encodeURIComponent(o.img || '');
    if (im.getAttribute('src') !== src) im.setAttribute('src', src);
    im.className = 'k' + o.kind;
    if (M.edit.habillage) im.classList.add('mode-' + modeVisuel(o));
  }
}

function placerPlateau(v, lateral, capture, plein) {
  if (!M.edit.habillage) {
    v.classList.toggle('pip', capture && !plein);
    return;
  }
  const cadre = v.parentElement;
  cadre.classList.toggle('pip', capture && !plein);
  const parDefaut = [0, 0, 1280, 720];
  const t = M.cur.a + M.t - M.cur.o;
  const cadrage = lateral && !capture && !plein
    ? (M.edit.recadrages?.find(r => r.src === M.cur.src && t >= r.a && t < r.b)?.rect || parDefaut)
    : null;
  if (!cadrage) {
    cadre.removeAttribute('style');
    for (const p of ['left', 'top', 'width', 'height']) v.style.removeProperty(p);
    return;
  }
  const [x, y, w, h] = cadrage;
  const gauche = clamp(lateral.split || 640, 320, 960);
  const k = Math.min(gauche / w, 720 / h);
  Object.assign(cadre.style, {
    left: `${(gauche - k * w) / 25.6}%`,
    top: `${(720 - k * h) / 14.4}%`,
    width: `${k * w / 12.8}%`,
    height: `${k * h / 7.2}%`,
  });
  Object.assign(v.style, {
    left: `${-100 * x / w}%`,
    top: `${-100 * y / h}%`,
    width: `${128000 / w}%`,
    height: `${72000 / h}%`,
  });
}

/* ---------- aperçu ---------- */
function activer(src) {
  for (const [s, v] of Object.entries(M.vids)) { v.style.display = s === src ? 'block' : 'none'; if (s !== src && !v.paused) v.pause(); }
  return M.vids[src];
}
function allerA(T, lecture) {
  if (!M.clips.length) return;
  T = clamp(T, 0, Math.max(0, M.total - 0.001)); M.t = T;
  const r = toSrc(T); M.cur = r.clip;
  const v = activer(r.clip.src), ts = r.clip.a + (T - r.clip.o);
  if (Math.abs(v.currentTime - ts) > 0.04) v.currentTime = ts;
  if (lecture) v.play().catch(() => {});
  majVue(!(drag && drag.type === 'scrub'));
}
function jouer() {
  if (!M || !M.clips.length) return;
  if (M.t >= M.total - 0.05) allerA(0);
  M.playing = true; M.vids[M.cur.src].play().catch(() => {}); q('#mtPlay').textContent = 'Pause'; requestAnimationFrame(boucle);
}
/* vitesse de lecture de l'aperçu (x1 à x3), gardée d'une session à l'autre */
function setVitesseMt(v) {
  vitesseMt = v; stock.set('mtVitesse', v);
  if (M) Object.values(M.vids).forEach(x => { x.preservesPitch = true; x.playbackRate = v; });
  rendreVitessesMt(); toast('x' + String(v).replace('.', ','));
}
function rendreVitessesMt() {
  const n = q('#mtVitesses'); if (!n) return;
  n.innerHTML = VITESSES_MT.map(v => `<button data-v="${v}" class="${v === vitesseMt ? 'sel' : ''}">${String(v).replace('.', ',')}x</button>`).join('');
}
function pause() { if (!M) return; M.playing = false; Object.values(M.vids).forEach(v => v.pause()); q('#mtPlay').textContent = 'Lecture'; }
function boucle() {
  if (!M?.playing) return;
  const c = M.cur, v = M.vids[c.src], ts = v.currentTime;
  if (ts >= c.b - 0.01 * vitesseMt || v.ended) {
    const i = M.clips.indexOf(c), n = M.clips[i + 1];
    if (!n) { pause(); M.t = M.total; majVue(); return; }
    M.cur = n; M.t = n.o;
    const vn = activer(n.src);
    if (!(n.src === c.src && Math.abs(vn.currentTime - n.a) < 0.12)) vn.currentTime = n.a;
    vn.play().catch(() => {});
  } else { M.t = c.o + (ts - c.a); v.volume = clamp(Math.min((ts - c.a) / 0.02, (c.b - ts) / 0.02), 0, 1); }
  majVue(true);
  requestAnimationFrame(boucle);
}
function majVue(suivre) {
  const tete = q('#mtTete'); if (tete) tete.style.left = (M.t * M.pxs) + 'px';
  q('#mtTc').innerHTML = `<b>${fmt(M.t)}</b> / ${fmt(M.total)}`;
  let capture = false, plein = false, lateral = null;
  for (const o of M.overlays) {
    const im = M.images.get(o.id); if (!im) continue;
    const e = ovTemps(o), vu = !!e && M.t >= e.S && M.t < e.E;
    im.classList.toggle('vu', vu);
    if (!vu) continue;
    if (M.edit.habillage) {
      const mode = modeVisuel(o);
      im.style.transform = '';
      im.style.opacity = 1;
      if (mode === 'side') { lateral = o; im.style.setProperty('--split', `${clamp(o.split || 640, 320, 960) / 12.8}%`); }
      else if (mode === 'pip') capture = true;
      else if (mode === 'full') plein = true;
    } else if (o.kind === 'S') { capture = true; im.style.opacity = clamp(Math.min((M.t - e.S) / 0.25, (e.E - M.t) / 0.25), 0, 1); im.style.transform = ''; }
    else {
      const p = clamp(Math.min((M.t - e.S) / 0.3, (e.E - M.t) / 0.3), 0, 1);
      im.style.opacity = 1; im.style.transform = `translateX(${(o.kind === 'P' ? 1 : -1) * (1 - p) * (o.kind === 'P' ? 43 : 47)}%)`;
    }
  }
  const v = M.cur && M.vids[M.cur.src];
  if (v) placerPlateau(v, lateral, capture, plein);
  const st = q('#mtSt');
  if (st) {
    const cue = M.sousTitres && M.cues ? M.cues.find(c => M.t >= c.a && M.t < c.b) : null;
    const t = cue ? cue.texte : '';
    if (st.textContent !== t) st.textContent = t;
    st.style.display = t ? '' : 'none';
  }
  if (suivre) {
    const s = q('#mtScroll'), x = M.t * M.pxs;
    if (x < s.scrollLeft + 20 || x > s.scrollLeft + s.clientWidth - 60) s.scrollLeft = Math.max(0, x - 100);
  }
}

/* ---------- timeline ---------- */
function rendre() {
  synchroniserVisuels();
  layout(); corrigerMots(); calculerSousTitres();
  const px = M.pxs, W = Math.ceil(M.total * px) + 80;
  const pas = px >= 12 ? 5 : px >= 5 ? 10 : 30;
  let ticks = '';
  for (let t = 0; t <= M.total; t += pas) ticks += `<div class="tick" style="left:${t * px}px">${Math.floor(t / 60)}:${String(Math.floor(t % 60)).padStart(2, '0')}</div>`;
  const clips = M.clips.map((c, i) => {
    const col = COUL[M.sources.indexOf(c.src) % COUL.length];
    return `<div class="mt-clip ${M.sel === c.id ? 'sel' : ''}" data-id="${c.id}" style="left:${c.o * px}px;width:${Math.max(3, c.d * px - 1)}px;background:${col}" title="${esc(fmt(c.a) + ' → ' + fmt(c.b) + ' (' + c.d.toFixed(2) + ' s)')}">
      <i class="hg"></i><span class="lib">${esc(texteClip(c))}</span><span class="num">${i + 1}</span><i class="hd"></i></div>`;
  }).join('');
  const ovs = k => M.overlays.filter(o => k.includes(o.kind)).map(o => {
    const e = ovTemps(o);
    if (!e) return '';
    return `<div class="mt-ov ${o.kind} ${M.selOv === o.id ? 'sel' : ''}" data-ov="${esc(o.id)}" style="left:${e.S * px}px;width:${Math.max(6, (e.E - e.S) * px)}px" title="${esc(nomVisuel(o) + ' : ' + fmt(e.S) + ' → ' + fmt(e.E))}">${esc(nomVisuel(o))}<i class="hd"></i></div>`;
  }).join('');
  const reps = tousRepères().map(r => {
    const col = couleurRep(r), titre = [fmt(r.S), r.type === 'moment' ? (CATS[r.cat] || CATS.fort)[0] : r.type === 'repère' ? 'Repère' : 'Commentaire', r.texte, r.dehors ? '(passage coupé)' : ''].filter(Boolean).join(' : ');
    const forme = r.type === 'moment' ? 'm' : r.type === 'repère' ? 'r' : 'c';
    return `<div class="mt-rep ${forme} ${M.selRep === r.k ? 'sel' : ''} ${r.dehors ? 'hors' : ''}" data-k="${esc(r.k)}" style="left:${r.S * px}px;${r.E != null ? `width:${Math.max(8, (r.E - r.S) * px)}px;` : ''}--c:${col}" title="${esc(titre)}"></div>`;
  }).join('');
  q('#mtCanvas').style.width = W + 'px';
  q('#mtCanvas').innerHTML = `<div class="mt-regle" id="mtRegle" style="width:${W}px">${ticks}</div>
    <div class="mt-lane rep" style="width:${W}px"><span class="lbl">Repères</span>${reps}</div>
    <div class="mt-piste" style="width:${W}px">${clips}</div>
    ${M.edit.habillage
      ? `<div class="mt-lane" style="width:${W}px"><span class="lbl">Cartes</span>${ovs(['P'])}</div>
         <div class="mt-lane" style="width:${W}px"><span class="lbl">Captures</span>${ovs(['S'])}</div>`
      : `<div class="mt-lane" style="width:${W}px"><span class="lbl">Cartes et captures</span>${ovs(['P', 'S'])}</div>`}
    <div class="mt-lane" style="width:${W}px"><span class="lbl">Bandeaux</span>${ovs(['T'])}</div>
    <div class="mt-tete" id="mtTete" style="left:${M.t * px}px"></div>`;
  majPanneau(); majVue();
}
function xDe(e) { const r = q('#mtCanvas').getBoundingClientRect(); return e.clientX - r.left; }

function demarrer(e) {
  if (!M) return;
  const h = e.target.closest('i.hg, i.hd'), clipEl = e.target.closest('.mt-clip'), ovEl = e.target.closest('.mt-ov'), repEl = e.target.closest('.mt-rep');
  q('#mtCanvas').setPointerCapture(e.pointerId);
  if (repEl) {
    const r = tousRepères().find(x => x.k === repEl.dataset.k); if (!r) return;
    M.selRep = r.k; M.sel = null; M.selOv = null; M.onglet = 'edition';
    if (r.type === 'repère') { const m = M.marks.find(x => 'mark:' + x.id === r.k); snapshot(); drag = { type: 'markM', m, x0: e.clientX, S0: r.S, mod: false }; }
    else drag = { type: 'scrub' };
    allerA(r.S); rendre(); return;
  }
  if (ovEl) {
    const o = M.overlays.find(x => x.id === ovEl.dataset.ov), t = ovTemps(o);
    M.selOv = o.id; M.sel = null; M.selRep = null; M.onglet = 'edition'; snapshot();
    if (!M.playing && !h) allerA(Math.min(t.S + 0.32, (t.S + t.E) / 2));
    drag = { type: h ? 'ovD' : 'ovM', o, x0: e.clientX, S0: t.S, d0: o.d, mod: false };
    rendre(); return;
  }
  if (clipEl) {
    const c = M.clips.find(x => x.id === clipEl.dataset.id);
    M.sel = c.id; M.selOv = null; M.selRep = null;
    if (h) { snapshot(); drag = { type: h.classList.contains('hg') ? 'trimL' : 'trimR', c, x0: e.clientX, a0: c.a, b0: c.b, mod: false }; rendre(); return; }
    rendre(); allerA(xDe(e) / M.pxs, M.playing); drag = { type: 'scrub' }; return;
  }
  M.sel = null; M.selOv = null; M.selRep = null; drag = { type: 'scrub' };
  allerA(xDe(e) / M.pxs, M.playing); rendre();
}
function bouger(e) {
  if (!drag || !M) return;
  const dx = (e.clientX - (drag.x0 ?? e.clientX)) / M.pxs;
  if (drag.type === 'scrub') { allerA(xDe(e) / M.pxs, M.playing); return; }
  drag.mod = true;
  if (drag.type === 'trimL') {
    let a = clamp(drag.a0 + dx, 0, drag.b0 - 0.2); a = aimanter(drag.c.src, a, 'start'); drag.c.a = clamp(a, 0, drag.b0 - 0.2);
  } else if (drag.type === 'trimR') {
    let b = clamp(drag.b0 + dx, drag.a0 + 0.2, dureeSrc(drag.c.src)); b = aimanter(drag.c.src, b, 'end'); drag.c.b = clamp(b, drag.a0 + 0.2, dureeSrc(drag.c.src));
  } else if (drag.type === 'ovD') {
    drag.o.d = Math.max(M.edit.habillage ? 1 / (M.edit.fps || FPS) : 1, +(drag.d0 + dx).toFixed(3));
  } else if (drag.type === 'ovM' || drag.type === 'markM') {
    const S = clamp(drag.S0 + dx, 0, Math.max(0, M.total - 0.05)), r = toSrc(S), cible = drag.o || drag.m;
    if (r) { cible.src = r.clip.src; cible.at = +(r.clip.a + (S - r.clip.o)).toFixed(3); }
  }
  rendre(); allerA(M.t);
}
function finir() {
  if (!drag) return;
  const d = drag; drag = null;
  if (d.mod) { planifier(); if (d.type === 'trimL') allerA(d.c.o); else if (d.type === 'trimR') allerA(Math.max(d.c.o, d.c.o + d.c.d - 1.2)); }
  else if (d.type !== 'scrub') M.hist.pop();
}

/* ---------- actions ---------- */
function couper() {
  const r = toSrc(M.t); if (!r) return;
  const c = r.clip, dt = M.t - c.o;
  if (dt < 0.15 || c.d - dt < 0.15) return notif('Place la tête de lecture à l\'intérieur d\'un plan');
  snapshot();
  const ts = +(c.a + dt).toFixed(3);
  const n = { id: uid(), src: c.src, a: ts, b: c.b, why: c.why };
  c.b = ts; M.clips.splice(r.i + 1, 0, n); M.sel = n.id; rendre(); planifier();
}
function supprimer() {
  if (M.selRep?.startsWith('mark:')) { snapshot(); M.marks = M.marks.filter(m => 'mark:' + m.id !== M.selRep); M.selRep = null; rendre(); planifier(); return; }
  if (M.selRep) return notif('Les commentaires et moments se modifient dans la revue (touche T pour y revenir)');
  if (M.selOv) { snapshot(); M.overlays = M.overlays.filter(o => o.id !== M.selOv); M.selOv = null; rendre(); planifier(); return; }
  if (!M.sel) return notif('Sélectionne un plan (clic sur la timeline)');
  const i = M.clips.findIndex(c => c.id === M.sel); if (i < 0) return;
  snapshot(); const t = M.clips[i].o; M.clips.splice(i, 1); M.sel = null; rendre(); allerA(Math.min(t, M.total - 0.01)); planifier();
}
function deplacer(dir) {
  const i = M.clips.findIndex(c => c.id === M.sel); const j = i + dir;
  if (i < 0 || j < 0 || j >= M.clips.length) return;
  snapshot(); [M.clips[i], M.clips[j]] = [M.clips[j], M.clips[i]]; rendre(); planifier();
}
function ajouterRepere() {
  const r = toSrc(M.t); if (!r) return;
  snapshot();
  const m = { id: uid(), label: '', src: r.clip.src, at: +(r.clip.a + (M.t - r.clip.o)).toFixed(2) };
  M.marks.push(m); M.selRep = 'mark:' + m.id; M.sel = null; M.selOv = null; M.onglet = 'edition'; rendre(); planifier();
  setTimeout(() => q('#mtLabel')?.focus(), 30);
}
function original() {
  if (!confirm('Revenir au plan d\'origine ? Tes retouches seront perdues (annulables avec Ctrl+Z).')) return;
  snapshot();
  M.clips = M.original.keep.map(k => ({ id: uid(), src: k.source, a: k.start, b: k.end, why: k.why || '' }));
  M.overlays = M.original.overlays.map(o => ({ ...o })); M.marks = []; M.corrections = M.edit.corrections_transcript || []; M.sel = null; M.selOv = null; M.selRep = null; rendre(); allerA(0); planifier();
}
function zoom(p) { M.pxs = clamp(p, 1, 30); stock.set('mt.pxs', M.pxs); q('#mtZoom').value = M.pxs; rendre(); }

async function chargerImageVisuel(file) {
  if (!file || !['image/png', 'image/jpeg', 'image/webp'].includes(file.type)) {
    throw new Error('Choisis une image PNG, JPEG ou WebP.');
  }
  const im = await createImageBitmap(file);
  try {
    const k = Math.min(1, 1920 / im.width, 1080 / im.height);
    const ca = document.createElement('canvas');
    ca.width = Math.max(1, Math.round(k * im.width));
    ca.height = Math.max(1, Math.round(k * im.height));
    ca.getContext('2d').drawImage(im, 0, 0, ca.width, ca.height);
    return ca.toDataURL('image/webp', 0.92);
  } finally { im.close(); }
}

async function importerVisuel(kind, original = null) {
  const input = q('#mtFileVisuel');
  const montage = M;
  const depart = Math.min(M.t, Math.max(0, M.total - 0.05));
  input.value = '';
  input.onchange = async () => {
    const file = input.files[0];
    if (!file) return;
    try {
      const img = await chargerImageVisuel(file);
      if (M !== montage) return;
      if (original && !M.overlays.includes(original)) return;
      const r = toSrc(depart);
      if (!r) return;
      snapshot();
      if (original) original.img = img;
      else {
        const ov = { id: uid(), label: file.name.replace(/\.[^.]+$/, ''), kind, src: r.clip.src,
          at: +(r.clip.a + depart - r.clip.o).toFixed(3), d: Math.min(6, M.total - depart), img };
        M.overlays.push(ov); M.selOv = ov.id; M.sel = null; M.selRep = null;
      }
      M.onglet = 'edition'; rendre(); planifier();
    } catch (err) { notif(err?.message || 'Impossible d’ouvrir cette image.'); }
  };
  input.click();
}

/* ---------- panneau de droite ---------- */
function majPanneau() {
  if (!M) return;
  const reps = tousRepères();
  q('#mtOngEdition').classList.toggle('sel', M.onglet === 'edition'); q('#mtOngReperes').classList.toggle('sel', M.onglet === 'reperes');
  q('#mtOngReperes').textContent = `Repères (${reps.length})`;
  if (M.onglet === 'reperes') return listeReperes(reps);
  const el = q('#mtInsp');
  const c = M.clips.find(x => x.id === M.sel), o = M.overlays.find(x => x.id === M.selOv), r = reps.find(x => x.k === M.selRep);
  if (r) {
    const k = r.type === 'moment' ? (CATS[r.cat] || CATS.fort)[0] : r.type === 'repère' ? 'Repère' : 'Commentaire';
    const mark = r.type === 'repère';
    el.innerHTML = `<div class="l">${esc(k)}${r.resolu ? ' (résolu)' : ''}</div>
      <div class="v"><b>${fmt(r.S)}</b> dans le montage${r.dehors ? ' <span style="color:var(--warn)">(passage coupé, repère posé au raccord)</span>' : ''}</div>
      ${mark ? `<label><span class="l">Texte du repère</span><input type="text" id="mtLabel" value="${esc(r.texte)}" placeholder="Ex : couper ici, ajouter la carte…" style="width:100%;background:var(--panel2);border:1px solid var(--line2);border-radius:6px;padding:6px 8px"></label>`
        : `<div class="txt">${esc(r.texte) || '(sans texte)'}</div><div class="aide">${esc(r.auteur)}${r.media ? ', sur ' + esc(court(r.media)) : ''}, à ${fmt(r.t)} de ce fichier.<br>Se modifie dans la revue (touche <kbd>T</kbd> pour y revenir).</div>`}
      <div class="aide">Temps source : ${esc(court(r.src))}, ${fmt(r.at)}</div>
      ${mark ? '<div class="btns"><button class="btn danger" id="mtSup">Supprimer le repère</button></div><div class="aide">Glisse le repère sur la timeline pour le déplacer.</div>' : ''}`;
    q('#mtLabel')?.addEventListener('change', ev => { snapshot(); const m = M.marks.find(x => 'mark:' + x.id === r.k); m.label = ev.target.value.trim(); rendre(); planifier(); });
  } else if (o) {
    const e = ovTemps(o);
    const mini = M.edit.habillage ? 1 / (M.edit.fps || FPS) : 1;
    el.innerHTML = `<div class="l">${TYPES_VISUEL[o.kind] || 'Visuel'}</div><div class="v"><b>${esc(nomVisuel(o))}</b></div>
      <div class="rang"><label><span class="l">Début (s)</span>${e ? `<input type="number" step="any" min="0" value="${+e.S.toFixed(3)}" id="mtOvStart">` : 'Hors montage'}</label>
      <label><span class="l">Durée (s)</span><input type="number" step="any" min="${mini}" value="${+o.d.toFixed(3)}" id="mtOvD"></label></div>
      ${M.edit.habillage ? `<label class="mt-visuel-mode"><span class="l">Position à l’écran</span><select id="mtOvMode">${Object.entries(MODES_VISUEL[o.kind] || {}).map(([v,t]) => `<option value="${v}" ${v === modeVisuel(o) ? 'selected' : ''}>${t}</option>`).join('')}</select></label>` : ''}
      <div class="aide">Glisse le visuel pour le déplacer. Tire son bord droit pour régler sa durée.</div>
      <div class="btns">${M.edit.habillage ? '<button class="btn" id="mtRemplaceVisuel">Remplacer l’image</button>' : ''}<button class="btn danger" id="mtSup">Supprimer le visuel</button></div>`;
    const debut = q('#mtOvStart');
    if (debut) debut.onchange = ev => {
      const t = clamp(+ev.target.value, 0, Math.max(0, M.total - mini)), r = toSrc(t);
      if (!r || !Number.isFinite(t)) return rendre();
      snapshot(); o.src = r.clip.src; o.at = +(r.clip.a + t - r.clip.o).toFixed(3);
      allerA(t + Math.min(0.32, o.d / 2)); rendre(); planifier();
    };
    q('#mtOvD').onchange = ev => { snapshot(); o.d = Math.max(mini, +ev.target.value || mini); rendre(); planifier(); };
    const mode = q('#mtOvMode'), remplacer = q('#mtRemplaceVisuel');
    if (mode) mode.onchange = ev => { snapshot(); o.mode = ev.target.value; rendre(); planifier(); };
    if (remplacer) remplacer.onclick = () => importerVisuel(o.kind, o);
  } else if (c) {
    const i = M.clips.indexOf(c);
    el.innerHTML = `<div class="l">Plan ${i + 1} sur ${M.clips.length}</div>
      <div class="v">${M.sources.indexOf(c.src) === 0 ? 'Prise 1' : 'Prise ' + (M.sources.indexOf(c.src) + 1)} <span style="color:var(--txt3)">${esc(c.src)}</span></div>
      <div class="rang"><label><span class="l">Début source (s)</span><input type="number" step="0.01" id="mtA" value="${c.a.toFixed(2)}"></label>
      <label><span class="l">Fin source (s)</span><input type="number" step="0.01" id="mtB" value="${c.b.toFixed(2)}"></label></div>
      <div class="v">${c.d.toFixed(2)} s, de ${fmt(c.o)} à ${fmt(c.o + c.d)} dans le montage</div>
      <div class="l">Texte</div><div class="txt" id="mtTexte">${esc(texteClip(c)) || '(rien)'}</div>
      <div class="btns"><button class="btn" id="mtEditTexte">Modifier le texte</button></div>
      ${c.why ? `<div class="l">Pourquoi</div><div class="aide">${esc(c.why)}</div>` : ''}
      <div class="btns"><button class="btn" id="mtAv">◀ Avant</button><button class="btn" id="mtAp">Après ▶</button><button class="btn danger" id="mtSup">Supprimer le plan</button></div>`;
    const modifier = q('#mtEditTexte');
    const editable = motsDe(c.src).some(([, s]) => s >= c.a - 0.01 && s < c.b);
    modifier.disabled = !editable;
    modifier.onclick = () => ouvrirEditionTexte(c);
    q('#mtA').onchange = ev => { const v = +ev.target.value; if (v >= 0 && v < c.b - 0.1) { snapshot(); c.a = v; rendre(); planifier(); } else rendre(); };
    q('#mtB').onchange = ev => { const v = +ev.target.value; if (v > c.a + 0.1 && v <= dureeSrc(c.src)) { snapshot(); c.b = v; rendre(); planifier(); } else rendre(); };
    q('#mtAv').onclick = () => deplacer(-1); q('#mtAp').onclick = () => deplacer(1);
  } else {
    const visuels = M.edit.habillage ? M.overlays.map(o => ({ o, e: ovTemps(o) }))
      .filter(v => v.e).sort((a, b) => a.e.S - b.e.S) : [];
    el.innerHTML = `${visuels.length ? `<div class="l">Visuels dans le montage</div>
      <div class="mt-visuels">${visuels.map(({ o, e }) => `<button class="mt-liste-visuel" data-visuel-id="${esc(o.id)}">
      <span>${fmt(e.S)}</span><span>${esc(nomVisuel(o))}</span><small>${TYPES_VISUEL[o.kind] || ''}</small></button>`).join('')}</div>` : ''}
      <div class="aide"><b>Comment retoucher</b><br>
      Clic sur un plan : le sélectionner et s'y placer.<br>
      Tirer le bord gauche ou droit d'un plan : le raccourcir ou le rallonger. Les plans suivants se recollent tout seuls. L'aimant cale le bord sur les mots.<br>
      <kbd>S</kbd> coupe le plan à la tête de lecture, puis supprime la partie en trop avec <kbd>Suppr</kbd>.<br>
      Les cartes (jaune, vert, violet) se déplacent en les glissant et suivent le plan sous elles.<br>
      <kbd>M</kbd> pose un repère à la tête de lecture.<br>
      <kbd>Espace</kbd> lecture, <kbd>←</kbd> <kbd>→</kbd> image par image (<kbd>Maj</kbd> : 1 s), <kbd>Ctrl</kbd>+<kbd>Z</kbd> annuler, <kbd>Ctrl</kbd>+<kbd>S</kbd> enregistrer avec copie, <kbd>+</kbd> <kbd>-</kbd> zoom.<br><br>
      Les retouches s'enregistrent toutes seules dans <code>revue/montage/</code>. Ensuite : « Envoyer à Claude » pour qu'il rende la nouvelle version.</div>`;
    el.querySelectorAll('[data-visuel-id]').forEach(button => button.onclick = () => {
      const o = M.overlays.find(v => v.id === button.dataset.visuelId), e = ovTemps(o);
      M.selOv = o.id;
      allerA(e.S + Math.min(0.32, (e.E - e.S) / 2)); rendre();
      q('#mtScroll').scrollLeft = Math.max(0, e.S * M.pxs - 100);
    });
  }
  const sup = q('#mtSup'); if (sup) sup.onclick = supprimer;
}
function ouvrirEditionTexte(c, focusIndex) {
  const zone = q('#mtTexte'), modifier = q('#mtEditTexte');
  const mots = motsDe(c.src), corriges = M.motsCorriges[c.src];
  pause();
  modifier.textContent = 'Terminer la correction';
  modifier.onclick = () => { majPanneau(); q('#mtEditTexte').focus(); };
  zone.innerHTML = corriges.map(([w, s], index) => {
    if (s < c.a - 0.01 || s >= c.b) return '';
    const original = mots[index][0];
    const supprimer = w === '' ? ' class="mt-mot-supprime"' : '';
    return `<button type="button" data-mot="${index}"${supprimer} title="${esc(original)}">${esc(w || original)}</button>`;
  }).join(' ');
  const premier = zone.querySelector(focusIndex == null ? '[data-mot]' : `[data-mot="${focusIndex}"]`);
  premier?.focus();
  zone.onclick = ev => {
    const bouton = ev.target.closest('[data-mot]');
    if (!bouton) return;
    zone.querySelector('form')?.remove();
    const index = +bouton.dataset.mot, [original, start, end] = mots[index];
    const form = document.createElement('form');
    form.innerHTML = `<label>Remplacer « ${esc(original)} »<input name="texte" type="text" maxlength="200" value="${esc(corriges[index][0])}"></label>
      <button class="btn" type="submit">Appliquer</button>
      <button class="btn" type="button">Annuler</button>
      <div class="aide">Laisse le champ vide pour masquer ce mot dans les sous-titres.</div>`;
    zone.append(form);
    const input = form.elements.texte;
    const annulerMot = () => { form.remove(); bouton.focus(); };
    form.querySelector('[type=button]').onclick = annulerMot;
    input.onkeydown = ev => { if (ev.key === 'Escape') { ev.preventDefault(); annulerMot(); } };
    input.focus(); input.select();
    form.onsubmit = ev => {
      ev.preventDefault();
      const texte = input.value.trim();
      if (texte === corriges[index][0]) return annulerMot();
      snapshot();
      M.corrections = M.corrections.filter(m => m.source !== c.src || m.index !== index);
      if (texte !== original) M.corrections.push({ source: c.src, index, original, start, end, texte });
      rendre(); planifier(); ouvrirEditionTexte(c, index);
    };
  };
}
function listeReperes(reps) {
  const el = q('#mtInsp');
  const f = (id, nom) => `<label class="mt-f"><input type="checkbox" data-f="${id}" ${M.filtres[id] ? 'checked' : ''}> ${nom}</label>`;
  el.innerHTML = `<div class="mt-filtres">${f('moments', 'Moments forts')}${f('comms', 'Commentaires')}${f('marks', 'Mes repères')}</div>
    <button class="btn" id="mtAddRep" style="align-self:flex-start">+ Repère à la tête de lecture <kbd>M</kbd></button>
    ${reps.length ? reps.map(r => {
      const k = r.type === 'moment' ? (CATS[r.cat] || CATS.fort)[0] : r.type === 'repère' ? 'Repère' : 'Commentaire';
      return `<div class="mt-row ${M.selRep === r.k ? 'sel' : ''} ${r.dehors ? 'hors' : ''}" data-k="${esc(r.k)}"><i style="background:${couleurRep(r)}"></i>
        <div><div class="t"><b>${fmt(r.S)}</b> ${esc(k)}${r.dehors ? ' (coupé)' : ''}</div><div class="x">${esc(r.texte) || '<span style="color:var(--txt3)">(sans texte)</span>'}</div></div></div>`;
    }).join('') : '<div class="aide">Aucun repère. Les commentaires et moments forts posés dans la revue (sur les rendus ou sur les prises) apparaissent ici, à leur place dans le montage.</div>'}`;
  el.querySelectorAll('[data-f]').forEach(c => c.onchange = () => { M.filtres[c.dataset.f] = c.checked; rendre(); });
  q('#mtAddRep').onclick = ajouterRepere;
  el.querySelectorAll('.mt-row').forEach(row => row.onclick = () => {
    const r = tousRepères().find(x => x.k === row.dataset.k); if (!r) return;
    M.selRep = r.k; M.sel = null; M.selOv = null; allerA(r.S); rendre();
    const s = q('#mtScroll'), x = r.S * M.pxs; if (x < s.scrollLeft || x > s.scrollLeft + s.clientWidth - 40) s.scrollLeft = Math.max(0, x - 120);
  });
}

/* ---------- enregistrement ---------- */
function etatSave(t, cls) { const e = q('#mtEtat'); e.textContent = t; e.className = 'mt-etat ' + (cls || ''); }
function planifier() { etatSave('Modifié…', 'sale'); clearTimeout(tSave); tSave = setTimeout(() => sauverMontage(), 600); }
async function sauverMontage(copie) {
  if (!M) return false;
  clearTimeout(tSave);
  tSave = null;
  const corps = {
    format: 'montage-manuel', base: M.f, sources: M.sources, modifie: new Date().toISOString(), duree: +M.total.toFixed(3),
    keep: M.clips.map(c => ({ source: c.src, start: +c.a.toFixed(3), end: +c.b.toFixed(3), why: c.why || '' })),
    overlays: M.overlays.map(o => ({ id: o.id, kind: o.kind, src: o.src, at: o.at, d: o.d, img: o.img,
      label: o.label, mode: o.mode, split: o.split })),
    corrections_transcript: M.corrections,
    reperes: M.marks.map(m => ({ id: m.id, label: m.label || '', src: m.src, at: m.at })),
  };
  const ecriture = sauvegarde.then(async () => {
    const r = await fetch('/api/montage?p=' + encodeURIComponent(M.f) + (copie ? '&copie=1' : ''), { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(corps) });
    const j = await r.json(); if (!r.ok || !j.ok) throw new Error();
    return j;
  });
  sauvegarde = ecriture.catch(() => {});
  try {
    const j = await ecriture;
    M.fichier = j.fichier; M.copie = j.copie;
    etatSave('Enregistré à ' + new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) + ' (' + fmt(M.total) + ')');
    return true;
  } catch { etatSave('Non enregistré', 'err'); return false; }
}
async function enregistrerAvecCopie() {
  if (await sauverMontage(true)) notif('Montage enregistré' + (M.copie ? ', copie : ' + M.copie : ''));
  else notif('Échec de l\'enregistrement : le serveur tourne-t-il ?');
}
async function envoyer() {
  if (!await sauverMontage()) return;
  if (!etat.asset) return notif('Ouvre d\'abord un média dans la bibliothèque (le plus récent du dossier rendus/)');
  $('#messageEnvoi').value = `Montage manuel : applique ${M.fichier} (durée ${fmt(M.total)}) et rends la nouvelle version, sans écraser les précédentes.`;
  $('#btnEnvoyerClaude').click();
}

/* ---------- interface ---------- */
function construire() {
  q('#montage').innerHTML = `
  <div class="mt-main">
    <div class="mt-scene-wrap"><div class="mt-scene" id="mtScene"></div></div>
    <div class="mt-transport">
      <button class="btn primaire" id="mtPlay">Lecture</button>
      <span class="mt-tc" id="mtTc"></span>
      <div class="vitesses" id="mtVitesses" title="Vitesse : touches 1, 2, 3 (x1, x2, x3), 4 = x1,5"></div>
      <span class="sep"></span>
      <button class="btn" id="mtCut" title="Couper le plan à la tête de lecture (S)">Couper <kbd>S</kbd></button>
      <button class="btn" id="mtDel" title="Supprimer le plan, la carte ou le repère sélectionné (Suppr)">Supprimer <kbd>Suppr</kbd></button>
      <button class="btn" id="mtUndo" title="Annuler (Ctrl+Z)">Annuler</button>
      <button class="btn" id="mtRedo" title="Rétablir (Ctrl+Maj+Z)">Rétablir</button>
      <button class="btn" id="mtMark" title="Poser un repère à la tête de lecture (M)">Repère <kbd>M</kbd></button>
      <span class="sep"></span>
      <button class="btn" id="mtAimant" title="Caler les bords des plans sur les mots">Aimant</button>
      <button class="btn" id="mtStBtn" title="Sous-titres dans l'aperçu">Sous-titres</button>
      <details class="mt-add-visuel" id="mtAddVisuel" hidden><summary class="btn">Ajouter un visuel</summary>
        <div class="mt-add-choix"><button class="btn" data-visuel="P">Carte</button><button class="btn" data-visuel="S">Capture</button><button class="btn" data-visuel="T">Bandeau</button></div>
      </details>
      <input type="file" id="mtFileVisuel" accept="image/png,image/jpeg,image/webp" hidden>
      <label style="display:flex;align-items:center;gap:6px;color:var(--txt3);font-size:12px">Zoom <input type="range" id="mtZoom" min="1" max="30" step="1" style="width:110px"></label>
      <span class="esp"></span>
      <span class="mt-etat" id="mtEtat"></span>
      <button class="btn" id="mtSave" title="Enregistrer et garder une copie horodatée (Ctrl+S)">Enregistrer <kbd>Ctrl</kbd>+<kbd>S</kbd></button>
      <button class="btn" id="mtOrig">Plan d'origine</button>
      <button class="btn primaire" id="mtEnvoi">Envoyer à Claude</button>
    </div>
    <div class="mt-tl"><div class="mt-scroll" id="mtScroll"><div class="mt-canvas" id="mtCanvas"></div></div></div>
  </div>
  <aside class="mt-side"><h3><span class="mt-tabs"><button id="mtOngEdition" class="sel">Édition</button><button id="mtOngReperes">Repères</button></span><span style="flex:1"></span><button class="btn" id="mtFermer" title="Retour à la revue (T)">Fermer</button></h3><div class="corps" id="mtInsp"></div></aside>`;
  q('#mtPlay').onclick = () => M?.playing ? pause() : jouer();
  rendreVitessesMt();
  q('#mtVitesses').addEventListener('click', e => { const b = e.target.closest('button'); if (b) setVitesseMt(+b.dataset.v); });
  q('#mtCut').onclick = () => M && couper(); q('#mtDel').onclick = () => M && supprimer();
  q('#mtUndo').onclick = () => M && annuler(); q('#mtRedo').onclick = () => M && retablir();
  q('#mtMark').onclick = () => M && ajouterRepere();
  q('#mtAimant').onclick = () => { M.aimant = !M.aimant; stock.set('mt.aimant', M.aimant); q('#mtAimant').classList.toggle('on', M.aimant); };
  q('#mtZoom').oninput = e => M && zoom(+e.target.value);
  q('#mtStBtn').onclick = () => { if (!M) return; M.sousTitres = !M.sousTitres; stock.set('mt.st', M.sousTitres); q('#mtStBtn').classList.toggle('on', M.sousTitres); majVue(); };
  q('#mtAddVisuel').onclick = ev => {
    const bouton = ev.target.closest('[data-visuel]');
    if (M && bouton) { q('#mtAddVisuel').open = false; importerVisuel(bouton.dataset.visuel); }
  };
  q('#mtSave').onclick = () => M && enregistrerAvecCopie();
  q('#mtOrig').onclick = () => M && original();
  q('#mtEnvoi').onclick = () => M && envoyer();
  q('#mtFermer').onclick = fermer;
  q('#mtOngEdition').onclick = () => { if (M) { M.onglet = 'edition'; majPanneau(); } };
  q('#mtOngReperes').onclick = () => { if (M) { M.onglet = 'reperes'; majPanneau(); } };
  const cv = q('#mtCanvas');
  cv.addEventListener('pointerdown', demarrer); cv.addEventListener('pointermove', bouger);
  cv.addEventListener('pointerup', finir); cv.addEventListener('pointercancel', finir);
}
MT.ouvrir = async () => {
  if (!q('#mtCanvas')) construire();
  if (etat.asset) video.pause();
  q('#montage').hidden = false; MT.actif = true; $('#btnMontage').classList.add('on');
  if (!M) {
    etatSave('Chargement…', 'sale');
    if (!await charger()) { fermer(); return; }
    q('#mtZoom').value = M.pxs; q('#mtAimant').classList.toggle('on', M.aimant); q('#mtStBtn').classList.toggle('on', M.sousTitres);
    etatSave(M.manuelCharge ? 'Retouches reprises' : 'Plan d\'origine, rien de modifié');
    if (!M.manuelCharge && !M.overlays.length && M.edit.habillage) notif('Aucun visuel chargé');
  }
};
function fermer() { if (M) pause(); q('#montage').hidden = true; MT.actif = false; $('#btnMontage').classList.remove('on'); }
MT.basculer = () => MT.actif ? fermer() : MT.ouvrir();

/* clavier : Ctrl+Z et Ctrl+S marchent partout dans le montage, même quand un champ a le focus */
window.addEventListener('keydown', e => {
  if (!MT.actif) return;
  const touche = (e.key || '').toLowerCase(), code = e.code;
  const mod = e.ctrlKey || e.metaKey;
  if (e.target.closest?.('#mtTexte form')) {
    if (!(mod && (touche === 's' || code === 'KeyS'))) return;
    e.preventDefault(); e.stopPropagation();
    e.target.closest('form').requestSubmit();
    enregistrerAvecCopie();
    return;
  }
  if (e.target.closest?.('#mtEditTexte, #mtTexte [data-mot]') && (touche === ' ' || touche === 'enter')) return;
  if (mod && (touche === 's' || code === 'KeyS')) { e.preventDefault(); e.stopPropagation(); if (M) enregistrerAvecCopie(); return; }
  if (mod && (touche === 'z' || code === 'KeyZ') && !e.altKey) {
    e.preventDefault(); e.stopPropagation();
    if (document.activeElement?.matches?.('input, textarea, select')) document.activeElement.blur();
    if (M) e.shiftKey ? retablir() : annuler();
    return;
  }
  if (mod && (touche === 'y' || code === 'KeyY')) { e.preventDefault(); e.stopPropagation(); if (M) retablir(); return; }
  if (e.target.matches?.('input, textarea, select')) { if (e.key === 'Escape') e.target.blur(); return; }
  e.stopPropagation();
  if (mod || e.altKey || !M) return;
  const k = e.key;
  if (k === ' ' || k === 'k' || k === 'K') { e.preventDefault(); M.playing ? pause() : jouer(); }
  else if (k === '1' || k === '2' || k === '3' || k === '4' || k === '0') { e.preventDefault(); setVitesseMt({ 1: 1, 2: 2, 3: 3, 4: 1.5, 0: 1 }[k]); }
  else if (k === 's' || k === 'S') { e.preventDefault(); couper(); }
  else if (k === 'm' || k === 'M') { e.preventDefault(); ajouterRepere(); }
  else if (k === 'Delete' || k === 'Backspace') { e.preventDefault(); supprimer(); }
  else if (k === 'ArrowLeft') { e.preventDefault(); pause(); allerA(M.t - (e.shiftKey ? 1 : 1 / FPS)); }
  else if (k === 'ArrowRight') { e.preventDefault(); pause(); allerA(M.t + (e.shiftKey ? 1 : 1 / FPS)); }
  else if (k === '+' || k === '=') zoom(M.pxs + 1);
  else if (k === '-') zoom(M.pxs - 1);
  else if (k === 'Home') allerA(0);
  else if (k === 'End') allerA(M.total);
  else if (k === 't' || k === 'T' || k === 'Escape') fermer();
}, true);
window.addEventListener('beforeunload', () => { if (M && tSave) sauverMontage(); });
})();
