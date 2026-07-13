#!/usr/bin/env python3
"""Système d'audit d'un run : trace TOUS les agents, leur travail, le flux
d'information jusqu'à la création du coupon.

Usage :
  PYTHONPATH=src python3 scripts/audit_run.py [journal.jsonl | runId]
  (sans argument : prend le run le plus récent)

Produit : un rapport texte (stdout) + data/audit_<runid>.md + data/audit_<runid>.html
"""
import json, sys, glob, os
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parents[1]
WF_DIR = Path("/root/.claude/projects/-home-user-betting-/a24e68df-da70-56fe-b651-133c9805c8a3/subagents/workflows")

ROLES = {
    "discovery":   ("Découverte", "🔎", "Trouve les vrais matchs du jour (Betano.de)"),
    "specialist":  ("Spécialiste recherche", "📚", "Collecte des données (forme, xG, H2H, cotes…)"),
    "desk":        ("Desk éditeur", "🧩", "Réconcilie/vérifie les faits + stats chiffrées"),
    "markets":     ("Analyste marchés", "📊", "Tous les marchés → opportunités de value (modèle croisé)"),
    "verify":      ("Vérificateur", "🕵️", "Contrôle adversarial (match à venir ? cote ? logique ?)"),
    "coordinator": ("Coordinateur", "🎯", "Classe et dé-corrèle les opportunités"),
    "final":       ("Synthèse/rédaction", "📝", "Construit le coupon + note finale"),
    "other":       ("Autre", "•", ""),
}


def classify(r):
    if not isinstance(r, dict):
        return "final" if isinstance(r, str) else "other"
    if "matches" in r: return "discovery"
    if "opportunities" in r: return "markets"
    if "verified_facts" in r: return "desk"
    if "verdict" in r: return "verify"
    if "ranked" in r: return "coordinator"
    if "facts" in r and "summary" in r: return "specialist"
    if "coupon" in r or "settled" in r or "verified_picks" in r: return "final"
    return "other"


def find_journal(arg):
    if arg:
        p = Path(arg)
        if p.is_file():
            return p
        cand = WF_DIR / arg / "journal.jsonl"
        if cand.is_file():
            return cand
        hits = list(WF_DIR.glob(f"*{arg}*/journal.jsonl"))
        if hits:
            return hits[0]
    journals = sorted(WF_DIR.glob("*/journal.jsonl"), key=lambda x: x.stat().st_mtime, reverse=True)
    return journals[0] if journals else None


def load(journal):
    started, results = [], []
    for line in journal.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            o = json.loads(line)
        except Exception:
            continue
        if o.get("type") == "started":
            started.append(o)
        elif o.get("type") == "result":
            results.append(o)
    return started, results


def audit(journal):
    started, results = load(journal)
    runid = journal.parent.name
    by_role = defaultdict(list)
    for o in results:
        by_role[classify(o.get("result"))].append(o.get("result"))

    n_started = len(started)
    n_done = len(results)
    n_error = max(0, n_started - n_done)

    # Flux (funnel)
    matches = []
    for d in by_role["discovery"]:
        matches += d.get("matches", [])
    n_specialists = len(by_role["specialist"])
    n_desks = len(by_role["desk"])
    opps = []
    for m in by_role["markets"]:
        opps += m.get("opportunities", [])
    verdicts = by_role["verify"]
    kept = [v for v in verdicts if v.get("verdict") == "keep"]
    dropped = [v for v in verdicts if v.get("verdict") == "drop"]

    return {
        "runid": runid, "journal": str(journal),
        "n_started": n_started, "n_done": n_done, "n_error": n_error,
        "roles": {k: len(v) for k, v in by_role.items()},
        "matches": matches,
        "n_specialists": n_specialists, "n_desks": n_desks,
        "n_opps": len(opps), "opps": opps,
        "n_verify": len(verdicts), "n_kept": len(kept), "n_dropped": len(dropped),
        "kept": kept, "dropped": dropped,
        "coordinator": len(by_role["coordinator"]),
        "final": len(by_role["final"]),
    }


def render_text(a):
    L = []
    L.append("=" * 66)
    L.append(f"AUDIT DU RUN — {a['runid']}")
    L.append("=" * 66)
    L.append(f"Agents lancés : {a['n_started']} | terminés : {a['n_done']} | "
             f"en échec/incomplets : {a['n_error']}")
    L.append("")
    L.append("--- QUI A TRAVAILLÉ (par rôle) ---")
    for role, n in sorted(a["roles"].items(), key=lambda kv: -kv[1]):
        name, emoji, desc = ROLES.get(role, (role, "•", ""))
        L.append(f"  {emoji} {name:<22} × {n:<3}  {desc}")
    L.append("")
    L.append("--- FLUX D'INFORMATION (entonnoir jusqu'au coupon) ---")
    L.append(f"  Matchs découverts .......... {len(a['matches'])}")
    L.append(f"  Agents spécialistes ........ {a['n_specialists']}  (données brutes + sources)")
    L.append(f"  Fiches de faits (desk) ..... {a['n_desks']}  (réconciliées + stats chiffrées)")
    L.append(f"  Opportunités de marché ..... {a['n_opps']}  (value, modèle × recherche)")
    L.append(f"  Vérifiées → gardées ........ {a['n_kept']} 🟢  / écartées {a['n_dropped']} 🔴")
    L.append(f"  Coordination ............... {a['coordinator']}  → construction du coupon")
    L.append("")
    if a["matches"]:
        L.append("--- MATCHS ANALYSÉS ---")
        for m in a["matches"][:20]:
            L.append(f"  • [{m.get('sport','?')}] {m.get('home','?')} vs {m.get('away','?')} "
                     f"({m.get('competition','?')})")
        L.append("")
    if a["dropped"]:
        L.append("--- POURQUOI DES PARIS ONT ÉTÉ ÉCARTÉS (échantillon) ---")
        for v in a["dropped"][:6]:
            iss = "; ".join(v.get("issues", [])[:1])[:110]
            L.append(f"  🔴 (conf {v.get('confidence')}) {iss}")
        L.append("")
    return "\n".join(L)


COUPON_HOWTO = """COMMENT LE COUPON EST CRÉÉ (algorithme) :
1. Chaque opportunité a : cote (Betano.de/Flashscore) + proba finale = BLEND(modèle Poisson, recherche).
2. VALUE = proba × cote − 1. On ne garde que value > 0.
3. VÉRIFICATION adversariale : match encore à venir ? cote réelle ? raisonnement solide ? (sinon écarté)
4. Le solveur choisit la combinaison de jambes (matchs DISTINCTS) dont la cote totale
   tombe dans la fourchette (défaut 1,95–3) en MAXIMISANT la proba conjointe (le plus « sûr »).
5. COMBIEN : 1 coupon combiné par jour (+ jusqu'à 2 paris simples cote 5–7 en option).
   Rien n'est forcé : si aucune combi ne rentre ou si rien ne passe la vérif → « rien à parier »."""


def render_html(a):
    def bar(n, mx, color):
        w = 0 if mx == 0 else int(100 * n / mx)
        return (f"<div class='bar'><div class='fill' style='width:{max(w,2)}%;background:{color}'></div>"
                f"<span>{n}</span></div>")
    mx = max(len(a["matches"]), a["n_specialists"], a["n_desks"], a["n_opps"], a["n_verify"], 1)
    roles_rows = ""
    for role, n in sorted(a["roles"].items(), key=lambda kv: -kv[1]):
        name, emoji, desc = ROLES.get(role, (role, "•", ""))
        roles_rows += f"<tr><td>{emoji} {name}</td><td class='num'>{n}</td><td class='desc'>{desc}</td></tr>"
    matches_html = "".join(
        f"<li><b>{m.get('sport','?')}</b> — {m.get('home','?')} vs {m.get('away','?')} "
        f"<span class='desc'>({m.get('competition','?')})</span></li>" for m in a["matches"][:24])
    dropped_html = "".join(
        f"<li>🔴 <span class='desc'>(conf {v.get('confidence')})</span> "
        f"{('; '.join(v.get('issues', [])[:1]))[:160]}</li>" for v in a["dropped"][:8])
    howto = COUPON_HOWTO.replace("\n", "<br>")
    return f"""<title>Audit du run — SportPredix</title>
<style>
:root {{ color-scheme: light dark; }}
body {{ font-family: system-ui, sans-serif; margin: 0; padding: 1.4rem; line-height: 1.45; }}
h1 {{ font-size: 1.35rem; margin: 0 0 .2rem; }} h2 {{ font-size: 1.05rem; margin: 1.3rem 0 .5rem; }}
.sub {{ opacity: .65; font-size: .85rem; margin-bottom: 1rem; }}
.kpi {{ display:flex; gap:.6rem; flex-wrap:wrap; margin:.6rem 0 1rem; }}
.kpi div {{ background: rgba(127,127,127,.1); border-radius:8px; padding:.5rem .8rem; }}
.kpi b {{ font-size:1.3rem; display:block; }}
table {{ border-collapse: collapse; width:100%; }}
td {{ padding:.28rem .5rem; border-bottom:1px solid rgba(127,127,127,.18); font-size:.92rem; }}
.num {{ text-align:right; font-variant-numeric: tabular-nums; font-weight:700; width:3rem; }}
.desc {{ opacity:.6; font-size:.85rem; }}
.funnel div.row {{ display:grid; grid-template-columns: 15rem 1fr; align-items:center; gap:.6rem; margin:.25rem 0; }}
.bar {{ position:relative; background: rgba(127,127,127,.12); border-radius:6px; height:1.5rem; }}
.fill {{ height:100%; border-radius:6px; }}
.bar span {{ position:absolute; right:.5rem; top:0; line-height:1.5rem; font-size:.82rem; font-weight:700; }}
.howto {{ background: rgba(37,99,235,.1); border-radius:8px; padding:.8rem 1rem; font-size:.92rem; }}
ul {{ margin:.3rem 0; padding-left:1.1rem; }} li {{ margin:.15rem 0; font-size:.9rem; }}
.disc {{ margin-top:1.2rem; font-size:.78rem; opacity:.6; }}
</style>
<h1>🔍 Audit du run — <code>{a['runid']}</code></h1>
<div class='sub'>Trace complète : agents, travail, flux d'information, construction du coupon.</div>
<div class='kpi'>
  <div><b>{a['n_started']}</b>agents lancés</div>
  <div><b>{a['n_done']}</b>terminés</div>
  <div><b>{a['n_error']}</b>échec/incomplets</div>
  <div><b>{len(a['matches'])}</b>matchs</div>
  <div><b>{a['n_opps']}</b>opportunités</div>
  <div><b>{a['n_kept']}</b>vérifiées 🟢</div>
</div>
<h2>👥 Qui a travaillé (par rôle)</h2>
<table>{roles_rows}</table>
<h2>🔻 Flux d'information (entonnoir jusqu'au coupon)</h2>
<div class='funnel'>
  <div class='row'><span>🔎 Matchs découverts</span>{bar(len(a['matches']), mx, '#2563eb')}</div>
  <div class='row'><span>📚 Spécialistes (données)</span>{bar(a['n_specialists'], mx, '#0891b2')}</div>
  <div class='row'><span>🧩 Fiches réconciliées</span>{bar(a['n_desks'], mx, '#7c3aed')}</div>
  <div class='row'><span>📊 Opportunités de value</span>{bar(a['n_opps'], mx, '#d97706')}</div>
  <div class='row'><span>🕵️ Gardées après vérif</span>{bar(a['n_kept'], mx, '#16a34a')}</div>
  <div class='row'><span>🔴 Écartées</span>{bar(a['n_dropped'], mx, '#dc2626')}</div>
</div>
<h2>🧮 Comment le coupon est créé</h2>
<div class='howto'>{howto}</div>
<h2>⚽ Matchs analysés</h2>
<ul>{matches_html or '<li>(aucun)</li>'}</ul>
<h2>🔴 Pourquoi des paris ont été écartés (échantillon)</h2>
<ul>{dropped_html or '<li>(aucun)</li>'}</ul>
<div class='disc'>Audit généré depuis le journal du run. ESTIMATIONS — aucun pari n'est sûr.</div>
"""


def merge(audits):
    """Fusionne plusieurs audits de runs en une seule vue système."""
    m = {"runid": "combine", "journal": "(plusieurs runs)",
         "n_started": 0, "n_done": 0, "n_error": 0, "roles": Counter(),
         "matches": [], "n_specialists": 0, "n_desks": 0, "n_opps": 0, "opps": [],
         "n_verify": 0, "n_kept": 0, "n_dropped": 0, "kept": [], "dropped": [],
         "coordinator": 0, "final": 0}
    seen = set()
    for a in audits:
        for k in ("n_started", "n_done", "n_error", "n_specialists", "n_desks",
                  "n_opps", "n_verify", "n_kept", "n_dropped", "coordinator", "final"):
            m[k] += a[k]
        for role, n in a["roles"].items():
            m["roles"][role] += n
        for mm in a["matches"]:
            key = f"{mm.get('home')}|{mm.get('away')}"
            if key not in seen:
                seen.add(key); m["matches"].append(mm)
        m["opps"] += a["opps"]; m["kept"] += a["kept"]; m["dropped"] += a["dropped"]
    m["roles"] = dict(m["roles"])
    return m


def main(argv):
    args = argv[1:]
    if len(args) > 1:
        audits = []
        for x in args:
            j = find_journal(x)
            if j:
                audits.append(audit(j))
        a = merge(audits)
    else:
        journal = find_journal(args[0] if args else None)
        if not journal:
            print("Aucun journal de run trouvé.")
            return 1
        a = audit(journal)
    print(render_text(a))
    print()
    print(COUPON_HOWTO)
    out_md = ROOT / "data" / f"audit_{a['runid']}.md"
    out_html = ROOT / "data" / f"audit_{a['runid']}.html"
    out_md.write_text(render_text(a) + "\n\n" + COUPON_HOWTO + "\n", encoding="utf-8")
    out_html.write_text(render_html(a), encoding="utf-8")
    print(f"\nÉcrit : {out_md.relative_to(ROOT)} et {out_html.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
