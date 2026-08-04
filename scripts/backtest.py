#!/usr/bin/env python3
"""Rejoue le modèle sur des années d'archives, contre les VRAIES cotes.

Le protocole en direct produira ~120 prédictions en 100 jours. Il en faudrait
~6 800 pour trancher sur le ROI. Ici, on en traite des dizaines de milliers en
quelques minutes — avec les cotes réelles de clôture, donc sans complaisance.

Déroulé, match par match, dans l'ordre chronologique strict :
  1. prédire avec les SEULES données antérieures au coup d'envoi
  2. comparer à la cote du marché, décider de parier ou non
  3. seulement ENSUITE, intégrer le résultat à l'historique

Toute inversion de ces trois étapes fait fuir le futur dans le passé et rend le
résultat flatteur et faux.

Usage :
  PYTHONPATH=src python3 scripts/backtest.py --ligues D1,E0,SP1,I1,F1 --de 2015 --a 2024
  PYTHONPATH=src python3 scripts/backtest.py --edge 0.05 --issues 1
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sportsbet import backtest as BT, devig as D, markets as M, rolling as R  # noqa: E402

ISSUES = ("1", "X", "2")


def arg(argv, nom, defaut, conv=str):
    return conv(argv[argv.index(nom) + 1]) if nom in argv else defaut


def rejouer(matchs: list, edge_min: float, issues: tuple,
            book: str, meilleure: bool, min_prob: float,
            arg_k: float = R.K_RETRECISSEMENT,
            calib=None, debut_test=None) -> tuple[list, dict, list]:
    """Le cœur : prédire, décider, puis seulement apprendre."""
    ligues: dict[str, R.Ligue] = {}
    paris, compte = [], {"vus": 0, "predits": 0, "sans_cote": 0, "sans_historique": 0}
    # Calibration mesurée sur TOUTES les prédictions, pas seulement sur les
    # paris retenus : ces derniers sont choisis là où le modèle s'écarte le plus
    # du marché, donc l'échantillon le plus defavorable. Juger le modèle dessus
    # revient à le condamner sur ses cas extrêmes.
    toutes = []

    # Repère de progression de saison, pour évaluer l'enjeu.
    par_ligue_saison: dict = {}
    for m in matchs:
        cle = (m.ligue, m.date.year if m.date.month >= 7 else m.date.year - 1)
        par_ligue_saison.setdefault(cle, []).append(m)
    rang = {}
    for cle, lst in par_ligue_saison.items():
        for i, mm in enumerate(sorted(lst, key=lambda x: x.date)):
            rang[id(mm)] = i / max(1, len(lst) - 1)

    for m in matchs:
        compte["vus"] += 1
        lg = ligues.setdefault(m.ligue, R.Ligue())
        a, b = lg.equipes[m.domicile], lg.equipes[m.exterieur]

        if not (a.pret and b.pret):
            compte["sans_historique"] += 1
            R.enregistrer(lg, m.domicile, m.exterieur, m.buts_dom, m.buts_ext,
                          m.stats, m.date)
            continue

        # ── 1. PRÉDIRE (rien d'autre que le passé) ────────────────────────
        lh, la = R.lambdas(lg, m.domicile, m.exterieur, k=arg_k)
        mk = M.all_goal_markets(lh, la, rho=-0.10)
        compte["predits"] += 1

        # Calibration : corrige le biais de compression vers le milieu.
        if calib is not None and calib.pret:
            mk = {k2: calib.corriger(v) for k2, v in mk.items()
                  if k2 in ISSUES} | {k2: v for k2, v in mk.items() if k2 not in ISSUES}
        for iss in ISSUES:
            toutes.append((mk.get(iss, 0.0), m.issue == iss, m.date))

        prog = rang.get(id(m), 0.0)
        enj_d = R.enjeu(lg, m.domicile, prog)
        enj_e = R.enjeu(lg, m.exterieur, prog)
        sans_enjeu = enj_d["sans_enjeu"] and enj_e["sans_enjeu"]

        # ── 2. DÉCIDER ────────────────────────────────────────────────────
        for issue in issues:
            p = mk.get(issue, 0.0)
            if p < min_prob:
                continue
            # On parie à la cote D'OUVERTURE : c'est ce qu'on fait en vrai, la
            # veille au soir. Parier à la clôture rendrait le CLV nul par
            # construction — on comparerait le prix pris à lui-même.
            cote = (m.meilleure_cote(issue, cloture=False) if meilleure
                    else m.cote(issue, book, cloture=False))
            if not cote:
                compte["sans_cote"] += 1
                continue
            # RÈGLE DURE : match sans enjeu, pas de 1X2 (leçon France 6-4).
            if sans_enjeu:
                continue
            if p * cote - 1.0 < edge_min:
                continue
            if debut_test and m.date < debut_test:
                continue
            paris.append(BT.Pari(match=m, issue=issue, prob=p, cote=cote,
                                 gagne=(m.issue == issue)))

        # ── 3. SEULEMENT MAINTENANT, APPRENDRE ────────────────────────────
        R.enregistrer(lg, m.domicile, m.exterieur, m.buts_dom, m.buts_ext,
                      m.stats, m.date)
    return paris, compte, toutes


def main(argv: list[str]) -> None:
    ligues = arg(argv, "--ligues", "D1,E0,SP1,I1,F1").split(",")
    de = arg(argv, "--de", 2015, int)
    a = arg(argv, "--a", 2024, int)
    edge = arg(argv, "--edge", 0.05, float)
    issues = tuple(arg(argv, "--issues", "1,X,2").split(","))
    book = arg(argv, "--book", "pinnacle")
    min_prob = arg(argv, "--min-prob", 0.10, float)
    meilleure = "--meilleure-cote" in argv
    k = arg(argv, "--k", R.K_RETRECISSEMENT, float)

    print(f"=== BANC D'ESSAI — {','.join(ligues)} · saisons {de}/{de+1} à {a}/{a+1} ===")
    print(f"Cote : {'MEILLEURE du marché' if meilleure else book} (clôture) | "
          f"edge minimal {edge*100:.0f} % | issues {','.join(issues)}\n")

    matchs = BT.charger(ligues, list(range(de, a + 1)))
    if not matchs:
        print("Aucune archive chargée."); return
    print(f"{len(matchs)} matchs chargés ({matchs[0].date} → {matchs[-1].date})")

    import datetime
    bascule = arg(argv, "--bascule", 0, int)
    calib = None
    if bascule:
        # PASSE 1 — apprendre la courbe de correction sur la période
        # d'entraînement UNIQUEMENT, sans parier.
        d_test = datetime.date(bascule, 7, 1)
        _, _, obs = rejouer(matchs, 9.9, issues, book, meilleure, min_prob, k)
        entr = [(pr, ok) for pr, ok, dt in obs if dt < d_test]
        calib = BT.Calibrateur()
        calib.entrainer(entr)
        print(f"  calibration apprise sur {len(entr)} prédictions "
              f"antérieures à {d_test} ({len(calib.seuils)} tranches)")
        print("  courbe : " + "  ".join(
            f"{x*100:.0f}→{y*100:.0f}" for x, y in calib.courbe()[::3]))
        # PASSE 2 — appliquer la correction, ne parier QUE hors échantillon.
        paris, c, toutes = rejouer(matchs, edge, issues, book, meilleure,
                                   min_prob, k, calib=calib, debut_test=d_test)
        toutes = [(pr, ok) for pr, ok, dt in toutes if dt >= d_test]
    else:
        paris, c, toutes = rejouer(matchs, edge, issues, book, meilleure, min_prob, k)
        toutes = [(pr, ok) for pr, ok, dt in toutes]
    print(f"  {c['predits']} prédits | {c['sans_historique']} écartés faute "
          f"d'historique | {len(paris)} paris déclenchés\n")

    r = BT.evaluer(paris)
    if not r.get("n"):
        print("Aucun pari : le seuil d'edge n'est jamais franchi."); return

    print(f"{'':22s}{'valeur':>12s}")
    print("-" * 34)
    print(f"{'Paris':22s}{r['n']:12d}")
    print(f"{'Mise totale':22s}{r['mise']:12.0f}")
    print(f"{'Profit':22s}{r['profit']:+12.1f}")
    print(f"{'ROI':22s}{r['roi']:+11.2f} %")
    print(f"{'Réussite':22s}{r['reussite']:11.1f} %")
    if r["clv_moyen"] is not None:
        print(f"{'CLV moyen':22s}{r['clv_moyen']:+11.2f} %")
        print(f"{'CLV positif':22s}{r['clv_positif']:11.1f} %")

    print("\n── CALIBRATION DU MODÈLE (toutes prédictions) ──")
    seaux: dict = {}
    for pr, ok in toutes:
        seaux.setdefault(min(90, int(pr * 10) * 10), []).append(ok)
    ecarts = []
    print(f"{'tranche':>12s} {'n':>7s} {'prédit':>8s} {'réel':>8s} {'écart':>8s}")
    for b in sorted(seaux):
        g = seaux[b]
        if len(g) < 100:
            continue
        pred = (b + 5) / 100
        reel = sum(g) / len(g)
        ecarts.append(abs(reel - pred))
        print(f"{b}-{b+10}%".rjust(12) + f" {len(g):7d} {pred*100:7.1f}% "
              f"{reel*100:7.1f}% {(reel-pred)*100:+7.1f}")
    if ecarts:
        print(f"   écart absolu moyen : {sum(ecarts)/len(ecarts)*100:.1f} pts")

    print("\n── CALIBRATION DES PARIS RETENUS ──")
    print(f"{'tranche':>12s} {'n':>6s} {'prédit':>8s} {'réel':>8s} {'écart':>8s}")
    for b in r["calibration"]:
        if b["n"] < 20:
            continue
        print(f"{b['tranche']:>12s} {b['n']:6d} {b['predit']*100:7.1f}% "
              f"{b['reel']*100:7.1f}% {(b['reel']-b['predit'])*100:+7.1f}")

    print("\n── PAR ISSUE ──")
    for i in issues:
        sous = [p for p in paris if p.issue == i]
        if not sous:
            continue
        s = BT.evaluer(sous)
        print(f"  {i} : {s['n']:5d} paris | ROI {s['roi']:+7.2f} % | "
              f"réussite {s['reussite']:5.1f} %"
              + (f" | CLV {s['clv_moyen']:+6.2f} %" if s['clv_moyen'] is not None else ""))

    print("\nLe CLV est l'indicateur qui compte : positif, il signale un vrai signal")
    print("bien avant que le ROI ne soit statistiquement lisible.")


if __name__ == "__main__":
    main(sys.argv)
