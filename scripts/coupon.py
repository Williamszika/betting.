#!/usr/bin/env python3
"""Coupon de prédiction téléchargeable — HTML autonome, statut évolutif.

Un coupon est généré juste après le workflow, avec le statut « en attente ».
Après vérification des résultats, on relance la même commande : le coupon est
régénéré au même emplacement avec les scores et le statut final.

  simple   1 sélection
  combiné  2+ sélections — les cotes se multiplient, les probabilités AUSSI
           (c'est pourquoi un combiné est presque toujours plus risqué qu'il
           n'en a l'air : deux paris à 55 % font un combiné à 30 %).

Usage :
  PYTHONPATH=src python3 scripts/coupon.py --date 2026-08-03
  PYTHONPATH=src python3 scripts/coupon.py --date 2026-08-03 --combine
  PYTHONPATH=src python3 scripts/coupon.py --state demo.json --out /tmp/x.html
"""
from __future__ import annotations

import datetime
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sportsbet import bankroll as BK  # noqa: E402

STATUTS = {
    "pending": ("EN ATTENTE", "#b45309", "#fef3c7", "⏳"),
    "won":     ("GAGNÉ", "#15803d", "#dcfce7", "🟢"),
    "lost":    ("PERDU", "#b91c1c", "#fee2e2", "🔴"),
    "void":    ("ANNULÉ", "#525252", "#f5f5f5", "⚪"),
}


def statut_coupon(sels: list[dict]) -> tuple[str, str, str, str]:
    """Statut global : un combiné perd si UNE seule jambe perd."""
    res = [s["result"] for s in sels]
    if any(r == "lost" for r in res):
        return STATUTS["lost"]
    if all(r == "won" for r in res):
        return STATUTS["won"]
    if all(r in ("won", "void") for r in res):
        return STATUTS["void"] if all(r == "void" for r in res) else STATUTS["won"]
    return STATUTS["pending"]


def heure_txt(s: dict) -> str:
    """Coup d'envoi À L'HEURE DU PARIEUR, pas à celle du stade.

    Un match roumain à 21h30 se joue à 20h30 en Allemagne : afficher l'heure
    locale du stade ferait rater le coup d'envoi.
    """
    ko = (s.get("kickoff_local") or "")[11:16]
    return f"· <b>{ko}</b>" if ko else ""


def ligne_html(s: dict, i: int, n: int) -> str:
    lib, coul, fond, ico = STATUTS.get(s["result"], STATUTS["pending"])
    veto = "VETO" in (s.get("stake_reason") or "").upper()
    cote = f"{s['odds']:.2f}" if s["odds"] > 1 else "—"
    mp = s.get("market_prob")
    marche = (f"<div class='marche'>marché {mp*100:.1f} % · "
              f"écart {(s['prob']-mp)*100:+.1f} pts</div>" if mp else "")
    note = ""
    if not s["playable"]:
        etiq = "REFUSÉ — CONTEXTE" if veto else "NON JOUÉ"
        note = (f"<div class='refus'><b>{etiq}</b> · "
                f"{html.escape(s.get('stake_reason', ''))}</div>")
    return f"""
    <div class="sel">
      <div class="sel-tete">
        <span class="num">{i}/{n}</span>
        <span class="match">{html.escape(s['match'])}</span>
        <span class="badge" style="color:{coul};background:{fond}">{ico} {lib}</span>
      </div>
      <div class="compet">{html.escape(s.get('competition', ''))}
        {heure_txt(s)}
        {('· ' + html.escape(s.get('score', ''))) if s.get('score') else ''}</div>
      <div class="pari">{html.escape(s['label'])}</div>
      <div class="chiffres">
        <div><span>Probabilité</span><b>{s['prob']*100:.1f} %</b></div>
        <div><span>Cote</span><b>{cote}</b></div>
        <div><span>Cote minimale</span><b>{s['min_odds']:.2f}</b></div>
        <div><span>Mise</span><b>{s['stake']:.2f} €</b></div>
      </div>
      {marche}{note}
    </div>"""


def rendu(st: dict, sels: list[dict], date: str, combine: bool) -> str:
    n = len(sels)
    joues = [s for s in sels if s["playable"] and s["stake"] > 0]
    mise = sum(s["stake"] for s in joues)
    lib, coul, fond, ico = statut_coupon(sels) if joues else STATUTS["pending"]
    if not joues:
        lib, coul, fond, ico = ("AUCUNE MISE", "#525252", "#f5f5f5", "🚫")

    if combine and len(joues) > 1:
        cote_tot, prob_tot = 1.0, 1.0
        for s in joues:
            cote_tot *= s["odds"]
            prob_tot *= s["prob"]
        mise = min(s["stake"] for s in joues)
        type_txt = f"COMBINÉ {len(joues)} MATCHS"
        recap = f"""
        <div class="recap-combine">
          <div><span>Cote totale</span><b>{cote_tot:.2f}</b></div>
          <div><span>Probabilité conjointe</span><b>{prob_tot*100:.1f} %</b></div>
          <div><span>Cote minimale utile</span><b>{1/(0.947*prob_tot):.2f}</b></div>
        </div>
        <p class="avert">Les cotes se multiplient — les probabilités aussi.
        {' × '.join(f"{s['prob']*100:.0f} %" for s in joues)} =
        <b>{prob_tot*100:.1f} %</b> de chances que TOUT passe.</p>"""
        gain = mise * cote_tot * 0.947
    else:
        type_txt = "SIMPLE" if n == 1 else f"{n} PRÉDICTIONS SÉPARÉES"
        recap = ""
        gain = sum(s["stake"] * s["eff_odds"] for s in joues)

    # Une fois le coupon réglé, le retour n'est plus « potentiel » : il vaut ce
    # qui a réellement été encaissé. Un combiné perdu rapporte zéro, même si le
    # produit des cotes reste affiché plus haut.
    regle = lib != "EN ATTENTE"
    if regle:
        if combine and len(joues) > 1:
            gain = gain if lib == "GAGNÉ" else 0.0
        else:
            gain = sum(s.get("payout", 0.0) for s in joues)

    d0 = datetime.date.fromisoformat(st["start"])
    jour = (datetime.date.fromisoformat(date) - d0).days + 1

    return f"""<meta charset="utf-8"><title>Coupon SportPredix — {date}</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{ font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
         background:#f1f5f9; margin:0; padding:24px; color:#0f172a; }}
  .ticket {{ max-width:640px; margin:0 auto; background:#fff; border-radius:14px;
            box-shadow:0 10px 30px rgba(0,0,0,.10); overflow:hidden; }}
  .tete {{ background:#0f172a; color:#fff; padding:20px 24px; }}
  .tete h1 {{ margin:0; font-size:18px; letter-spacing:.14em; }}
  .tete .meta {{ margin-top:6px; font-size:13px; color:#94a3b8; }}
  .statut {{ display:inline-block; margin-top:12px; padding:7px 16px;
            border-radius:999px; font-weight:700; font-size:14px;
            color:{coul}; background:{fond}; }}
  .corps {{ padding:8px 24px 24px; }}
  .sel {{ border-bottom:1px dashed #cbd5e1; padding:18px 0; }}
  .sel:last-child {{ border-bottom:none; }}
  .sel-tete {{ display:flex; align-items:center; gap:10px; flex-wrap:wrap; }}
  .num {{ font-size:11px; font-weight:700; color:#64748b; background:#f1f5f9;
         padding:3px 8px; border-radius:6px; }}
  .match {{ font-weight:700; font-size:16px; flex:1; }}
  .badge {{ padding:4px 11px; border-radius:999px; font-size:11px; font-weight:700; }}
  .compet {{ font-size:12px; color:#64748b; margin-top:3px; }}
  .pari {{ margin-top:10px; font-size:15px; font-weight:600; color:#1d4ed8; }}
  .chiffres {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(110px,1fr));
              gap:10px; margin-top:12px; }}
  .chiffres div {{ background:#f8fafc; border-radius:8px; padding:9px 11px; }}
  .chiffres span {{ display:block; font-size:11px; color:#64748b; }}
  .chiffres b {{ font-size:15px; }}
  .marche {{ margin-top:9px; font-size:12px; color:#7c3aed; }}
  .refus {{ margin-top:9px; font-size:12px; background:#fef2f2; color:#991b1b;
           border-left:3px solid #dc2626; padding:8px 11px; border-radius:0 6px 6px 0; }}
  .recap-combine {{ display:flex; gap:10px; flex-wrap:wrap; margin:16px 0 6px; }}
  .recap-combine div {{ flex:1; min-width:120px; background:#eff6ff; border-radius:8px;
                       padding:10px 12px; }}
  .recap-combine span {{ display:block; font-size:11px; color:#64748b; }}
  .recap-combine b {{ font-size:17px; color:#1d4ed8; }}
  .avert {{ font-size:12px; color:#92400e; background:#fffbeb; padding:10px 12px;
           border-radius:8px; }}
  .pied {{ background:#f8fafc; padding:18px 24px; border-top:1px solid #e2e8f0; }}
  .totaux {{ display:flex; justify-content:space-between; font-size:14px;
            padding:5px 0; }}
  .totaux b {{ font-size:16px; }}
  .avis {{ margin-top:14px; font-size:11px; color:#64748b; line-height:1.6; }}
  @media (prefers-color-scheme: dark) {{
    body {{ background:#0b1120; color:#e2e8f0; }}
    .ticket {{ background:#111827; }}
    .chiffres div, .pied {{ background:#1e293b; }}
    .num {{ background:#1e293b; color:#94a3b8; }}
    .sel {{ border-color:#334155; }}
    .pied {{ border-color:#334155; }}
    .recap-combine div {{ background:#1e293b; }}
    .avert {{ background:#292524; color:#fbbf24; }}
    .refus {{ background:#2a1215; color:#fca5a5; }}
  }}
</style>
<div class="ticket">
  <div class="tete">
    <h1>SPORTPREDIX · COUPON</h1>
    <div class="meta">{date} · jour {jour}/100 · {type_txt} · mode PAPER</div>
    <div class="statut">{ico} {lib}</div>
  </div>
  <div class="corps">
    {''.join(ligne_html(s, i, n) for i, s in enumerate(sels, 1))}
    {recap}
  </div>
  <div class="pied">
    <div class="totaux"><span>Mise totale</span><b>{mise:.2f} €</b></div>
    <div class="totaux"><span>Retour {'potentiel' if lib == 'EN ATTENTE' else 'réalisé'}
      (taxe 5,3 % déduite)</span><b>{gain:.2f} €</b></div>
    <div class="totaux"><span>Bankroll</span><b>{st['bankroll']:.2f} €</b>
      <span style="color:#64748b">(départ {st['bankroll_start']:.2f} €)</span></div>
    <div class="avis">
      La <b>cote minimale</b> est celle sous laquelle le pari est perdant d'avance,
      taxe allemande de 5,3 % incluse. Les probabilités sont des <b>estimations</b>
      statistiques, pas des certitudes.<br>
      Mode PAPER — aucun argent réellement engagé. Ce document n'est pas une
      invitation à parier. Aide : joueurs-info-service.fr · 09 74 75 13 13.
    </div>
  </div>
</div>"""


CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
FOND_CLAIR = (241, 245, 249)      # #f1f5f9, le fond de page


def en_image(html_path: Path, png_path: Path, largeur: int = 700) -> bool:
    """Capture le coupon en PNG partageable (WhatsApp, Telegram, SMS).

    Chromium ne sait pas ajuster sa fenêtre à la hauteur du contenu : on
    capture large, puis on recadre sur le contenu réel. Sans ce recadrage, le
    coupon flotte au sommet d'une image trois fois trop haute.
    """
    import subprocess
    ch = Path(CHROME)
    if not ch.exists():
        print(f"[info] Chromium introuvable ({CHROME}) — PNG non généré", file=sys.stderr)
        return False
    png_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            [str(ch), "--headless", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
             "--force-device-scale-factor=2", f"--window-size={largeur},2400",
             f"--screenshot={png_path}", f"file://{html_path.resolve()}"],
            capture_output=True, timeout=120,
        )
    except Exception as e:
        print(f"[info] capture impossible : {e}", file=sys.stderr)
        return False
    if not png_path.exists():
        return False

    try:
        from PIL import Image
    except ImportError:
        return True                     # image brute, sans recadrage
    im = Image.open(png_path).convert("RGB")
    w, h = im.size
    bas = h
    for y in range(h - 1, 0, -1):       # remonter jusqu'au dernier pixel de contenu
        ligne = im.crop((0, y, w, y + 1)).getcolors(w) or []
        if not (len(ligne) == 1 and ligne[0][1] == FOND_CLAIR):
            bas = min(h, y + 48)        # marge sous le ticket
            break
    im.crop((0, 0, w, bas)).save(png_path, "PNG", optimize=True)
    return True


def main(argv: list[str]) -> None:
    etat = Path(argv[argv.index("--state") + 1]) if "--state" in argv \
        else ROOT / "data" / "protocol.json"
    st = json.loads(etat.read_text(encoding="utf-8"))
    date = argv[argv.index("--date") + 1] if "--date" in argv else \
        datetime.date.today().isoformat()
    combine = "--combine" in argv

    sels = [p for p in st["predictions"] if p["date"] == date]
    if not sels:
        print(f"Aucune prédiction pour le {date}.")
        return

    out = Path(argv[argv.index("--out") + 1]) if "--out" in argv else \
        ROOT / "data" / "coupons" / f"coupon_{date}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(rendu(st, sels, date, combine), encoding="utf-8")

    lib = statut_coupon(sels)[0]
    joues = [s for s in sels if s["playable"] and s["stake"] > 0]
    # Un combiné est UNE mise unique ; des simples se cumulent.
    mise = (min((s["stake"] for s in joues), default=0.0)
            if combine and len(joues) > 1 else sum(s["stake"] for s in joues))
    print(f"Coupon écrit : {out}")
    print(f"  {len(sels)} sélection(s) · {len(joues)} jouée(s) · "
          f"mise {mise:.2f} € · statut {lib if joues else 'AUCUNE MISE'}")

    if "--no-png" not in argv:
        png = out.with_suffix(".png")
        if en_image(out, png):
            print(f"Image partageable : {png}")


if __name__ == "__main__":
    main(sys.argv)
