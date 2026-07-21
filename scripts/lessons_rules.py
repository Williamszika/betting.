#!/usr/bin/env python3
"""Parse data/lessons.md -> règles machine (hard/soft) pour le workflow.

Corrige la Faille n°1 : le script du workflow n'a pas accès au disque. Cet outil
(lancé par l'orchestrateur) lit lessons.md, en extrait les blocs ```rule {...}```,
et produit le JSON à passer via args au workflow :

  { "hardRules": [...], "softBlock": "…", "orphans": N, "invalid": N,
    "counts": {"hard": h, "soft": s} }

Une leçon (section `## …`) SANS bloc `rule` est « orpheline » (décorative, sans
effet sur le moteur) : on les compte et on les liste sur stderr — anti-Faille-n°1
permanent.

Usage :
  python3 scripts/lessons_rules.py            # JSON complet sur stdout
  python3 scripts/lessons_rules.py --args     # imprime juste {hardRules, softBlock} (à copier dans args)
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LESSONS = ROOT / "data" / "lessons.md"

RULE_BLOCK = re.compile(r"```rule\s*\n(.*?)```", re.DOTALL)
SECTION = re.compile(r"^##\s+", re.MULTILINE)


def load_rules():
    if not LESSONS.exists():
        return {"hardRules": [], "softBlock": "", "orphans": 0, "invalid": 0,
                "counts": {"hard": 0, "soft": 0}, "error": "lessons.md introuvable"}
    md = LESSONS.read_text(encoding="utf-8")
    blocks = RULE_BLOCK.findall(md)
    hard, soft, invalid = [], [], 0
    for raw in blocks:
        try:
            r = json.loads(raw)
        except Exception:
            invalid += 1
            continue
        if not r.get("pattern") or not r.get("action") or not r.get("severity"):
            invalid += 1
            continue
        (hard if r["severity"] == "hard" else soft).append(r)

    # Bloc SOFT (texte injecté dans les prompts).
    if soft:
        lines = ["LEÇONS À RESPECTER (issues de pertes réelles, non négociables) :"]
        for i, r in enumerate(soft, 1):
            lines.append(f"{i}. [{r.get('market') or 'tous marchés'}] {r.get('note', r['pattern'])}")
        lines.append("Si une prédiction contredit une de ces leçons, signale-le dans le rationale "
                     "et baisse la confiance en conséquence.")
        soft_block = "\n".join(lines)
    else:
        soft_block = ""

    # Orphelines : sections `## …` sans bloc rule associé.
    n_sections = len(SECTION.findall(md))
    orphans = max(0, n_sections - len(blocks))

    return {"hardRules": hard, "softBlock": soft_block, "orphans": orphans,
            "invalid": invalid, "counts": {"hard": len(hard), "soft": len(soft)}}


def main(argv):
    res = load_rules()
    # Diagnostic sur stderr (visible sans polluer le JSON de stdout).
    print(f"[lessons] {res['counts']['hard']} hard, {res['counts']['soft']} soft"
          + (f", ⚠️ {res['orphans']} leçon(s) orpheline(s) (sans règle -> sans effet)" if res.get('orphans') else "")
          + (f", ⚠️ {res['invalid']} bloc(s) rule invalide(s)" if res.get('invalid') else ""),
          file=sys.stderr)
    if "--args" in argv:
        print(json.dumps({"hardRules": res["hardRules"], "softBlock": res["softBlock"]}, ensure_ascii=False))
    else:
        print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main(sys.argv)
