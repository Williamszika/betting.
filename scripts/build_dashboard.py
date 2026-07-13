#!/usr/bin/env python3
"""Génère le tableau de bord de suivi des coupons (HTML coloré + Markdown).

Usage : PYTHONPATH=src python3 scripts/build_dashboard.py
Lit data/ledger.jsonl -> écrit data/tracking.html et data/tracking.md
Vert = gagné, Rouge = perdu, Gris = void, Ambre = en attente.
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sportsbet import ledger as L  # noqa: E402

LEDGER = ROOT / "data" / "ledger.jsonl"
HTML = ROOT / "data" / "tracking.html"
MD = ROOT / "data" / "tracking.md"

COLORS = {"won": "#16a34a", "lost": "#dc2626", "void": "#6b7280", "pending": "#d97706"}
LABEL = {"won": "GAGNÉ", "lost": "PERDU", "void": "VOID", "pending": "EN ATTENTE"}


def build():
    entries = L.load(LEDGER)
    r = L.record(entries)

    # --- Markdown ---
    md = ["# Suivi des coupons — SportPredix", "",
          f"**Bilan :** {r['won']} 🟢 · {r['lost']} 🔴 · {r['pending']} ⏳ — "
          f"réussite **{r['win_rate']:.0%}**, ROI **{r['roi']:+.1%}** "
          f"(profit {r['profit']:+.2f} u sur {r['staked']:.0f} u misées)", ""]
    for e in reversed(entries):
        emoji = {"won": "🟢", "lost": "🔴", "void": "⚪", "pending": "⏳"}.get(e.get("status"), "❔")
        md.append(f"### {emoji} {e.get('id')} — cote {e.get('total_odds', 0):.2f} ({e.get('status')})")
        for lg in e.get("legs", []):
            le = {"won": "🟢", "lost": "🔴", "void": "⚪", "pending": "⏳"}.get(lg.get("result"), "❔")
            md.append(f"- {le} {lg.get('match')} — {lg.get('market')} / {lg.get('pick')} @ {lg.get('odds')}"
                      + (f" — {lg.get('note')}" if lg.get('note') else ""))
        if e.get("retro"):
            rc = e["retro"]
            md.append(f"  - 🧠 **Rétro :** {rc.get('what_happened','')}")
            for feat in (rc.get("features_to_add") or []):
                md.append(f"    - ➕ à ajouter : {feat}")
        md.append("")
    MD.write_text("\n".join(md), encoding="utf-8")

    # --- HTML ---
    rows = []
    for e in reversed(entries):
        st = e.get("status", "pending")
        legs_html = ""
        for lg in e.get("legs", []):
            lc = COLORS.get(lg.get("result", "pending"), "#888")
            legs_html += (f"<div class='leg'><span class='dot' style='background:{lc}'></span>"
                          f"{lg.get('match')} — <b>{lg.get('pick')}</b> "
                          f"<span class='market'>({lg.get('market')})</span> @ {lg.get('odds')}"
                          + (f" <span class='note'>· {lg.get('note')}</span>" if lg.get('note') else "")
                          + "</div>")
        retro = ""
        if e.get("retro"):
            feats = "".join(f"<li>{x}</li>" for x in (e['retro'].get('features_to_add') or []))
            retro = (f"<div class='retro'>🧠 <b>Rétro :</b> {e['retro'].get('what_happened','')}"
                     + (f"<ul>{feats}</ul>" if feats else "") + "</div>")
        rows.append(
            f"<div class='card' style='border-left:6px solid {COLORS.get(st,'#888')}'>"
            f"<div class='head'><span class='badge' style='background:{COLORS.get(st,'#888')}'>"
            f"{LABEL.get(st, st)}</span> <b>{e.get('id')}</b> — cote {e.get('total_odds',0):.2f} "
            f"· proba est. {e.get('joint_prob',0):.0%}</div>{legs_html}{retro}</div>")

    html = f"""<title>Suivi des coupons — SportPredix</title>
<style>
:root {{ color-scheme: light dark; }}
body {{ font-family: system-ui, sans-serif; margin: 0; padding: 1.5rem; }}
h1 {{ margin: 0 0 .3rem; font-size: 1.4rem; }}
.summary {{ font-size: 1.05rem; margin-bottom: 1rem; opacity:.9; }}
.card {{ background: rgba(127,127,127,.08); border-radius: 10px; padding: .8rem 1rem; margin: .6rem 0; }}
.head {{ margin-bottom: .4rem; }}
.badge {{ color:#fff; padding: .1rem .5rem; border-radius: 6px; font-size:.72rem; font-weight:700; letter-spacing:.03em; }}
.leg {{ padding: .15rem 0; font-size:.95rem; }}
.dot {{ display:inline-block; width:.7rem; height:.7rem; border-radius:50%; margin-right:.5rem; vertical-align:middle; }}
.market {{ opacity:.6; font-size:.85rem; }}
.note {{ opacity:.7; font-style:italic; }}
.retro {{ margin-top:.4rem; padding:.4rem .6rem; background: rgba(217,119,6,.12); border-radius:6px; font-size:.9rem; }}
.retro ul {{ margin:.3rem 0 0 1rem; }}
.disc {{ margin-top:1.2rem; font-size:.8rem; opacity:.6; }}
</style>
<h1>📊 Suivi des coupons — SportPredix</h1>
<div class='summary'>Bilan : <b style='color:{COLORS['won']}'>{r['won']} gagnés</b> ·
<b style='color:{COLORS['lost']}'>{r['lost']} perdus</b> · {r['pending']} en attente —
réussite <b>{r['win_rate']:.0%}</b>, ROI <b>{r['roi']:+.1%}</b> (profit {r['profit']:+.2f} u)</div>
{''.join(rows) if rows else "<p>Aucun coupon enregistré pour le moment.</p>"}
<div class='disc'>ESTIMATIONS statistiques, pas des certitudes. Jeu responsable — joueurs-info-service.fr, 09 74 75 13 13.</div>
"""
    HTML.write_text(html, encoding="utf-8")
    print(f"Écrit : {HTML.relative_to(ROOT)} et {MD.relative_to(ROOT)}")
    print(L.render_text(entries))


if __name__ == "__main__":
    build()
