#!/usr/bin/env python3
"""Rapport de VALIDATION des prédictions (calibration + CLV + porte PAPER/REVIEW).

Usage : PYTHONPATH=src python3 scripts/validate.py
Produit : rapport texte (stdout) + data/validation.md
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sportsbet import ledger as L  # noqa
from sportsbet import validation as V  # noqa

LEDGER = ROOT / "data" / "ledger.jsonl"
OUT_MD = ROOT / "data" / "validation.md"


def main():
    entries = L.load(LEDGER)
    txt = V.render_text(entries)
    print(txt)

    g = V.gate(entries)
    preds = V.iter_predictions(entries)
    md = ["# Validation des prédictions — SportPredix", "",
          "> Mode **PAPER** : 0 € misé. On mesure si les prédictions sont crédibles.",
          f"> Ce rapport ne dit jamais « miser » — au mieux « REVIEW » (à analyser à froid).", "",
          f"**Porte : `{g['mode']}`** — {g['reason']}", "",
          f"- Prédictions réglées : **{len(preds)}**"]
    if preds:
        wins = sum(1 for p in preds if p["won"])
        md.append(f"- Réussite globale : **{wins}/{len(preds)}** ({round(wins / len(preds) * 100, 1)}%)")
    md += ["", "## Calibration (prédit vs réel)", "",
           "| Tranche | n | Prédit moyen | Réel | Écart |", "|---|---|---|---|---|"]
    cal = V.calibration(preds)
    if cal:
        for r in cal:
            md.append(f"| {r['tranche']} | {r['n']} | {r['predit_moyen']}% | {r['reel']}% | {r['ecart']:+.1f} pts |")
    else:
        md.append("| — | 0 | — | — | — |")
    clv = V.clv_report(preds)
    md += ["", "## CLV (bat-on la cote de clôture ?)", ""]
    if clv["n"]:
        md.append(f"- CLV moyen : **{clv['clv_moyen']:+.4f}** · positifs : {clv['clv_positifs']} (n={clv['n']})")
    else:
        md.append(f"- {clv['note']}")
    md += ["", "## Par contexte", "", "| Contexte | n | Réussite |", "|---|---|---|"]
    for r in V.by_context(preds):
        md.append(f"| {r['contexte']} | {r['n']} | {r['reussite']}% |")
    md += ["", "*Rappel : un CLV moyen > 0 sur 80+ prédictions réglées est le minimum "
           "pour parler d'edge. En dessous, les prédictions ne sont pas validées — et "
           "même validées, ça reste du PAPER, pas une invitation à miser.*", ""]
    OUT_MD.write_text("\n".join(md), encoding="utf-8")
    print(f"\nÉcrit : {OUT_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
