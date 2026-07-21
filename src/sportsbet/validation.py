"""Validation des prédictions : CALIBRATION + CLV + porte PAPER/REVIEW.

Objectif : mesurer si les prédictions sont CRÉDIBLES, sans miser (mode PAPER).
La « porte » ne dit JAMAIS « miser » — au mieux « REVIEW » (échantillon atteint,
à analyser à froid). C'est un outil de validation statistique, pas un feu vert.

- **Calibration** : quand le modèle annonce ~p%, l'issue se réalise-t-elle ~p%
  du temps ? (le vrai test de fiabilité).
- **CLV** (closing line value) : notre cote bat-elle la cote de CLÔTURE ?
  `clv = cote_prise / cote_cloture - 1`. CLV moyen > 0 = seul signal robuste
  qu'un edge existe. Nécessite `closing_odds` renseigné au règlement.

Stdlib pure, aucune dépendance.
"""
from __future__ import annotations

# Seuils du contrat (codés, pas « en tête »).
GATE = {"MIN_PREDICTIONS": 100, "MIN_SETTLED": 80, "MIN_CLV": 0.0}


def iter_predictions(entries: list[dict]) -> list[dict]:
    """Aplati les jambes RÉGLÉES (won/lost) en prédictions unitaires."""
    out = []
    for e in entries:
        for lg in e.get("legs", []):
            res = lg.get("result")
            if res not in ("won", "lost"):
                continue
            co = lg.get("closing_odds")
            out.append({
                "date": (e.get("id", "") or "")[:10],
                "match": lg.get("match", ""),
                "competition": lg.get("competition", ""),
                "context": lg.get("context_flag", "normal"),
                "market": lg.get("market", ""),
                "pick": lg.get("pick", ""),
                "est_prob": float(lg.get("est_prob") or 0.0),
                "odds": float(lg.get("odds") or 0.0),
                "closing_odds": (float(co) if co else None),
                "won": res == "won",
            })
    return out


def calibration(preds: list[dict]) -> list[dict]:
    """Regroupe par tranche de proba prédite (déciles) : prédit vs réel."""
    buckets: dict[int, dict] = {}
    for p in preds:
        b = min(90, int(p["est_prob"] * 10) * 10)  # 0-10, …, 90+
        d = buckets.setdefault(b, {"n": 0, "wins": 0, "sum_p": 0.0})
        d["n"] += 1
        d["wins"] += 1 if p["won"] else 0
        d["sum_p"] += p["est_prob"]
    rows = []
    for b in sorted(buckets):
        d = buckets[b]
        rows.append({
            "tranche": f"{b}-{b + 10}%",
            "n": d["n"],
            "predit_moyen": round(d["sum_p"] / d["n"] * 100, 1),
            "reel": round(d["wins"] / d["n"] * 100, 1),
            "ecart": round((d["wins"] / d["n"] - d["sum_p"] / d["n"]) * 100, 1),
        })
    return rows


def clv_report(preds: list[dict]) -> dict:
    """CLV moyen + part de CLV positifs (sur les prédictions avec cote de clôture)."""
    withco = [p for p in preds if p["closing_odds"] and p["closing_odds"] > 1]
    if not withco:
        return {"n": 0, "clv_moyen": None, "clv_positifs": "0/0",
                "note": "Aucune cote de clôture renseignée (closing_odds au règlement)."}
    clvs = [p["odds"] / p["closing_odds"] - 1 for p in withco]
    pos = sum(1 for c in clvs if c > 0)
    return {"n": len(withco), "clv_moyen": round(sum(clvs) / len(clvs), 4),
            "clv_positifs": f"{pos}/{len(withco)}"}


def by_context(preds: list[dict]) -> list[dict]:
    """Taux de réussite par contexte de match (normal/finale/barrage…)."""
    agg: dict[str, dict] = {}
    for p in preds:
        d = agg.setdefault(p["context"], {"n": 0, "wins": 0})
        d["n"] += 1
        d["wins"] += 1 if p["won"] else 0
    return [{"contexte": k, "n": v["n"], "reussite": round(v["wins"] / v["n"] * 100, 1)}
            for k, v in sorted(agg.items())]


def gate(entries: list[dict]) -> dict:
    """Porte : PAPER tant que l'échantillon/CLV ne sont pas au niveau. Jamais « miser »."""
    preds = iter_predictions(entries)
    total_logged = sum(len(e.get("legs", [])) for e in entries)
    settled = len(preds)
    clv = clv_report(preds)
    clv_ok = clv["clv_moyen"] is not None and clv["clv_moyen"] > GATE["MIN_CLV"]
    passes = (total_logged >= GATE["MIN_PREDICTIONS"]
              and settled >= GATE["MIN_SETTLED"] and clv_ok)
    return {
        "mode": "REVIEW" if passes else "PAPER",  # « REVIEW » = à analyser, PAS « miser »
        "total_logged": total_logged,
        "settled": settled,
        "clv_moyen": clv["clv_moyen"],
        "reason": (
            f"Échantillon atteint ({settled} réglées, CLV {clv['clv_moyen']}). À analyser à froid — "
            f"ce n'est PAS un feu vert pour miser."
            if passes else
            f"PAPER : {total_logged}/{GATE['MIN_PREDICTIONS']} prédictions, "
            f"{settled}/{GATE['MIN_SETTLED']} réglées, "
            f"CLV {'inconnu' if clv['clv_moyen'] is None else clv['clv_moyen']} (requis > {GATE['MIN_CLV']})."
        ),
    }


def render_text(entries: list[dict]) -> str:
    preds = iter_predictions(entries)
    g = gate(entries)
    lines = ["VALIDATION DES PRÉDICTIONS (mode PAPER — 0 € misé)", "=" * 60]
    lines.append(f"Porte : {g['mode']} — {g['reason']}")
    lines.append("")
    lines.append(f"Prédictions réglées : {len(preds)}")
    if preds:
        wins = sum(1 for p in preds if p["won"])
        lines.append(f"Réussite globale : {wins}/{len(preds)} ({round(wins / len(preds) * 100, 1)}%)")
    lines.append("")
    lines.append("— CALIBRATION (prédit vs réel) —")
    cal = calibration(preds)
    if cal:
        for r in cal:
            lines.append(f"  {r['tranche']:>8} | n={r['n']:>3} | prédit {r['predit_moyen']:>5}% | "
                         f"réel {r['reel']:>5}% | écart {r['ecart']:+.1f} pts")
    else:
        lines.append("  (pas encore de prédiction réglée)")
    lines.append("")
    lines.append("— CLV (bat-on la cote de clôture ?) —")
    clv = clv_report(preds)
    if clv["n"]:
        lines.append(f"  CLV moyen : {clv['clv_moyen']:+.4f} | positifs : {clv['clv_positifs']} (n={clv['n']})")
    else:
        lines.append(f"  {clv['note']}")
    lines.append("")
    lines.append("— PAR CONTEXTE —")
    for r in by_context(preds):
        lines.append(f"  {r['contexte']:>8} | n={r['n']:>3} | réussite {r['reussite']}%")
    return "\n".join(lines)
