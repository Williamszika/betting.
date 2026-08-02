#!/usr/bin/env python3
"""Protocole 100 jours — suivi complet : prédictions, résultats, bankroll.

  init     démarre l'expérience (remet tout à zéro, bankroll de départ)
  add      enregistre la prédiction du jour (avec mise calculée)
  settle   enregistre le résultat d'une prédiction (won/lost/void)
  report   état du protocole : jour N/100, bilan, bankroll, calibration

Usage :
  PYTHONPATH=src python3 scripts/protocol.py init --bankroll 10 --start 2026-08-03
  PYTHONPATH=src python3 scripts/protocol.py add --file pred.json
  PYTHONPATH=src python3 scripts/protocol.py settle --id 2026-08-03 --result won
  PYTHONPATH=src python3 scripts/protocol.py report
"""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sportsbet import bankroll as BK  # noqa: E402

STATE = ROOT / "data" / "protocol.json"
DAYS = 100

#: Fuseau de référence — celui du parieur, pas celui du stade.
TZ = ZoneInfo("Europe/Berlin")

#: Durée d'un match, coup d'envoi → coup de sifflet final.
#: 45 + 15 + 45 minutes, plus les arrêts de jeu : 2 h couvre largement.
DUREE_MATCH = datetime.timedelta(hours=2)


def fin_de_match(kickoff_iso: str) -> datetime.datetime | None:
    """Heure de FIN du match, dans le fuseau du parieur."""
    if not kickoff_iso:
        return None
    try:
        ko = datetime.datetime.fromisoformat(kickoff_iso)
    except ValueError:
        return None
    if ko.tzinfo is None:                     # sans fuseau : on suppose l'heure locale
        ko = ko.replace(tzinfo=TZ)
    return (ko + DUREE_MATCH).astimezone(TZ)


def date_de_verification(kickoff_iso: str, date_repli: str) -> str:
    """Le LENDEMAIN de la fin du match — pas le lendemain du coup d'envoi.

    Un match à 21h30 finit vers 23h30 : vérification le lendemain. Mais un match
    à 22h45 finit APRÈS MINUIT, donc un jour calendaire plus tard — le vérifier
    « le lendemain de la date affichée » reviendrait à le contrôler quelques
    heures seulement après le coup de sifflet, parfois avant.
    """
    fin = fin_de_match(kickoff_iso)
    base = fin.date() if fin else datetime.date.fromisoformat(date_repli)
    return (base + datetime.timedelta(days=1)).isoformat()


def maintenant() -> datetime.datetime:
    return datetime.datetime.now(TZ)


def _load() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {}


def _save(st: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding="utf-8")


def cmd_init(argv: list[str]) -> None:
    bk = float(argv[argv.index("--bankroll") + 1]) if "--bankroll" in argv else 10.0
    start = argv[argv.index("--start") + 1] if "--start" in argv else \
        datetime.date.today().isoformat()
    end = (datetime.date.fromisoformat(start) + datetime.timedelta(days=DAYS - 1)).isoformat()
    st = {
        "protocol": "100 jours", "start": start, "end": end, "days": DAYS,
        "bankroll_start": bk, "bankroll": bk, "mode": "PAPER",
        "tax_mode": "gross", "kelly_fraction": BK.DEFAULT_KELLY_FRACTION,
        "predictions": [], "bankroll_history": [
            {"date": start, "event": "démarrage", "amount": bk, "balance": bk}],
    }
    _save(st)
    print(f"Protocole initialisé : {start} → {end} ({DAYS} jours)")
    print(f"Bankroll de départ : {bk:.2f} € | mode PAPER | Kelly 1/"
          f"{round(1/BK.DEFAULT_KELLY_FRACTION)} | taxe {BK.TAX_RATE*100:.1f} %")


def cmd_add(argv: list[str]) -> None:
    """Ajoute la prédiction du jour. JSON attendu :
    {id, date, match, competition, market, label, prob, odds}"""
    st = _load()
    if not st:
        print("Protocole non initialisé (lancer `init`)."); return
    src = argv[argv.index("--file") + 1]
    p = json.loads(Path(src).read_text(encoding="utf-8"))
    if any(x["id"] == p["id"] for x in st["predictions"]):
        print(f"La prédiction {p['id']} existe déjà."); return

    prob = float(p["prob"])
    odds = float(p.get("odds") or 0.0)

    # Cote non relevée : on enregistre quand même. La prédiction ne rapporte
    # rien mais elle compte pour la CALIBRATION, qui ne dépend pas du prix.
    if odds <= 1.0:
        plan = BK.StakePlan(
            0.0, False, "cote Betano non relevée — enregistré pour la calibration",
            prob=prob, odds=0.0, eff_odds=0.0,
            min_odds=BK.min_odds_for_breakeven(prob, st.get("tax_mode", "gross")),
            bankroll=st["bankroll"])
    else:
        plan = BK.plan_stake(st["bankroll"], prob, odds,
                             fraction=st.get("kelly_fraction", 0.20),
                             mode=st.get("tax_mode", "gross"))

    # VETO CONTEXTUEL — le calcul dit oui, le terrain dit non.
    # Quand notre probabilité repose sur une donnée que le marché a déjà
    # dépassée (effondrement récent, changement d'entraîneur, cascade de
    # blessures), l'écart au marché n'est pas un avantage : c'est notre
    # retard. On enregistre la prédiction pour la calibration, mise à zéro.
    veto = argv[argv.index("--veto") + 1] if "--veto" in argv else ""
    if veto:
        plan = BK.StakePlan(0.0, False, f"VETO CONTEXTUEL — {veto}",
                            prob=prob, odds=odds, eff_odds=plan.eff_odds,
                            min_odds=plan.min_odds, edge=plan.edge,
                            kelly_full=plan.kelly_full, bankroll=st["bankroll"])
    ko = p.get("kickoff", "")
    fin = fin_de_match(ko)
    rec = {
        "id": p["id"], "date": p["date"], "match": p["match"],
        "competition": p.get("competition", ""), "market": p["market"],
        "label": p.get("label", p["market"]),
        # Heure du coup d'envoi telle que fournie (avec son fuseau d'origine),
        # convertie chez le parieur, plus la date à laquelle on pourra vérifier.
        "kickoff": ko,
        "kickoff_local": fin and (fin - DUREE_MATCH).isoformat(timespec="minutes") or "",
        "fin_local": fin.isoformat(timespec="minutes") if fin else "",
        "verifiable_le": date_de_verification(ko, p["date"]),
        "prob": round(prob, 4), "odds": odds,
        # Probabilité IMPLICITE DU MARCHÉ, marge retirée. C'est la seule
        # référence qui dise si le modèle apporte quelque chose ou s'il
        # récite le consensus. Facultative : souvent introuvable.
        "market_prob": round(float(p["market_prob"]), 4) if p.get("market_prob") else None,
        "market_ref": p.get("market_ref", ""),
        "eff_odds": round(plan.eff_odds, 3), "min_odds": round(plan.min_odds, 2),
        "edge": round(plan.edge, 4), "kelly_full": round(plan.kelly_full, 4),
        "stake": plan.stake, "playable": plan.playable, "stake_reason": plan.reason,
        "result": "pending", "settled": None, "payout": 0.0,
    }
    st["predictions"].append(rec)
    if plan.playable and plan.stake > 0:
        st["bankroll"] = round(st["bankroll"] - plan.stake, 2)
        st["bankroll_history"].append({"date": p["date"], "event": f"mise {p['match']}",
                                       "amount": -plan.stake, "balance": st["bankroll"]})
    _save(st)
    flag = f"MISE {plan.stake:.2f} €" if plan.playable else "NON JOUABLE"
    cote = f"cote {rec['odds']:.2f}" if rec["odds"] > 1 else "cote non relevée"
    print(f"[{rec['id']}] {rec['match']} — {rec['label']}")
    print(f"  proba {rec['prob']*100:.1f}% | {cote} (min {rec['min_odds']:.2f}) "
          f"| edge {rec['edge']*100:+.1f}% | {flag}")
    if rec["market_prob"]:
        d = (rec["prob"] - rec["market_prob"]) * 100
        print(f"  marché {rec['market_prob']*100:.1f}% ({rec['market_ref']}) "
              f"→ écart {d:+.1f} pts")
    print(f"  {plan.reason}")


def cmd_settle(argv: list[str]) -> None:
    st = _load()
    if not st:
        print("Protocole non initialisé."); return
    pid = argv[argv.index("--id") + 1]
    res = argv[argv.index("--result") + 1]
    score = argv[argv.index("--score") + 1] if "--score" in argv else ""
    rec = next((x for x in st["predictions"] if x["id"] == pid), None)
    if not rec:
        print(f"Prédiction {pid} introuvable."); return
    if rec["result"] != "pending":
        print(f"{pid} déjà réglée ({rec['result']})."); return

    # GARDE-FOU HORAIRE — ne jamais régler un match qui n'est pas fini.
    # Un score relevé en cours de match est un score faux : c'est exactement
    # ainsi qu'on enregistre une victoire sur un match qui finit 2-2.
    fin = fin_de_match(rec.get("kickoff", ""))
    if fin and maintenant() < fin and "--force" not in argv:
        reste = fin - maintenant()
        h, m = divmod(int(reste.total_seconds() // 60), 60)
        print(f"⛔ {pid} — {rec['match']} n'est pas terminé "
              f"(fin prévue {fin:%d/%m à %Hh%M}, dans {h}h{m:02d}).")
        print("   Le régler maintenant enregistrerait un score en cours. "
              "Utiliser --force uniquement si le match est réellement fini.")
        return

    rec["result"] = res
    rec["settled"] = datetime.date.today().isoformat()
    rec["score"] = score
    if rec["playable"] and rec["stake"] > 0:
        if res == "won":
            payout = round(rec["stake"] * rec["eff_odds"], 2)
            rec["payout"] = payout
            st["bankroll"] = round(st["bankroll"] + payout, 2)
            st["bankroll_history"].append({"date": rec["settled"],
                                           "event": f"gagné {rec['match']}",
                                           "amount": payout, "balance": st["bankroll"]})
        elif res == "void":
            st["bankroll"] = round(st["bankroll"] + rec["stake"], 2)
            st["bankroll_history"].append({"date": rec["settled"],
                                           "event": f"annulé {rec['match']}",
                                           "amount": rec["stake"], "balance": st["bankroll"]})
        else:
            st["bankroll_history"].append({"date": rec["settled"],
                                           "event": f"perdu {rec['match']}",
                                           "amount": 0.0, "balance": st["bankroll"]})
    _save(st)
    icon = {"won": "🟢", "lost": "🔴", "void": "⚪"}.get(res, "?")
    print(f"{icon} {pid} {rec['match']} — {res} {score} | bankroll {st['bankroll']:.2f} €")


def cmd_pending(argv: list[str]) -> None:
    """Ce qui est PRÊT à être vérifié — et ce qui doit encore attendre.

    La règle : on vérifie le lendemain de la FIN du match. Cette commande
    répond donc à la seule question utile au rendez-vous de 8h : sur quoi
    puis-je travailler ce matin ?
    """
    st = _load()
    if not st:
        print("Protocole non initialisé."); return
    now = maintenant()
    aujourdhui = now.date().isoformat()
    prets, attente = [], []
    for p in st["predictions"]:
        if p["result"] != "pending":
            continue
        (prets if p.get("verifiable_le", p["date"]) <= aujourdhui else attente).append(p)

    print(f"── {now:%A %d/%m %Hh%M} (heure de Berlin) ──\n")
    if prets:
        print(f"✅ PRÊT À VÉRIFIER ({len(prets)}) :")
        for p in prets:
            fin = p.get("fin_local", "")[:16].replace("T", " ")
            print(f"   {p['id']}  {p['match'][:34]:34s} {p['label'][:26]:26s}"
                  + (f"  fini {fin}" if fin else ""))
    else:
        print("✅ PRÊT À VÉRIFIER : rien.")
    if attente:
        print(f"\n⏳ PAS ENCORE ({len(attente)}) :")
        for p in attente:
            ko = p.get("kickoff_local", "")[:16].replace("T", " ")
            print(f"   {p['id']}  {p['match'][:34]:34s} "
                  + (f"coup d'envoi {ko}  " if ko else "")
                  + f"→ vérifiable le {p.get('verifiable_le', p['date'])}")


def cmd_report(argv: list[str]) -> None:
    st = _load()
    if not st:
        print("Protocole non initialisé."); return
    preds = st["predictions"]
    settled = [p for p in preds if p["result"] in ("won", "lost")]
    played = [p for p in settled if p["playable"] and p["stake"] > 0]
    won = [p for p in settled if p["result"] == "won"]

    d0 = datetime.date.fromisoformat(st["start"])
    day = (datetime.date.today() - d0).days + 1
    entete = (f"jour {min(day, DAYS)}/{DAYS}" if day >= 1
              else f"démarrage le {st['start']}")

    print(f"╔══ PROTOCOLE 100 JOURS — {entete} ══╗")
    print(f"  Période      : {st['start']} → {st['end']}   (mode {st['mode']})")
    print(f"  Bankroll     : {st['bankroll']:.2f} € (départ {st['bankroll_start']:.2f} €)")
    prof = round(st["bankroll"] - st["bankroll_start"], 2)
    roi = (st["bankroll"] / st["bankroll_start"] - 1) * 100 if st["bankroll_start"] else 0
    print(f"  Profit       : {prof:+.2f} €  ({roi:+.1f} %)")
    print()
    print(f"  Prédictions  : {len(preds)} émises | {len(settled)} réglées | "
          f"{len(preds)-len(settled)} en attente")
    if settled:
        print(f"  Résultats    : {len(won)} 🟢 / {len(settled)-len(won)} 🔴  "
              f"({len(won)/len(settled)*100:.0f} % de réussite)")
    sans_cote = [p for p in preds if p["odds"] <= 1]
    sous_seuil = [p for p in preds if not p["playable"] and p["odds"] > 1]
    print(f"  Jouables     : {len(played)} misées sur {len(settled)} réglées "
          f"| {len(sous_seuil)} sous le seuil | {len(sans_cote)} sans cote relevée")

    if settled:
        print("\n  ── CALIBRATION (le modèle dit-il vrai ?) ──")
        buckets: dict[int, list] = {}
        for p in settled:
            b = min(90, int(p["prob"] * 10) * 10)
            buckets.setdefault(b, []).append(p)
        for b in sorted(buckets):
            g = buckets[b]
            pred = sum(x["prob"] for x in g) / len(g) * 100
            real = sum(1 for x in g if x["result"] == "won") / len(g) * 100
            print(f"    {b}-{b+10}% | n={len(g):3d} | prédit {pred:5.1f}% | "
                  f"réel {real:5.1f}% | écart {real-pred:+5.1f} pts")

    # ── LE MODÈLE BAT-IL LE MARCHÉ ? ───────────────────────────────────────
    # Une calibration parfaite ne prouve RIEN si elle ne fait que recopier les
    # cotes. La seule question qui compte : notre probabilité s'écarte-t-elle
    # du marché, et quand elle s'en écarte, a-t-elle raison ?
    vs = [p for p in preds if p.get("market_prob")]
    if vs:
        gaps = [abs(p["prob"] - p["market_prob"]) for p in vs]
        moy = sum(gaps) / len(gaps) * 100
        print(f"\n  ── FACE AU MARCHÉ (n={len(vs)}) ──")
        print(f"    Écart absolu moyen : {moy:.1f} pts")
        if moy < 1.5:
            print("    → le modèle RÉCITE le marché. Aucun avantage possible :")
            print("      on paie la marge du bookmaker pour la même information.")
        vs_reg = [p for p in vs if p["result"] in ("won", "lost")]
        if vs_reg:
            desac = [p for p in vs_reg if abs(p["prob"] - p["market_prob"]) >= 0.03]
            if desac:
                gagne = sum(1 for p in desac
                            if (p["result"] == "won") == (p["prob"] > p["market_prob"]))
                print(f"    Désaccords ≥3 pts : {len(desac)} | "
                      f"le modèle a eu raison {gagne}/{len(desac)} fois "
                      f"({gagne/len(desac)*100:.0f} %)")
                print("      (50 % = le désaccord est du bruit ; il faut nettement plus)")
            else:
                print("    Aucun désaccord ≥3 pts encore réglé.")

    if preds:
        print("\n  ── 10 DERNIÈRES ──")
        for p in preds[-10:]:
            ic = {"won": "🟢", "lost": "🔴", "void": "⚪", "pending": "⏳"}[p["result"]]
            st_txt = f"{p['stake']:.2f}€" if p["playable"] else "  —  "
            cote = f"@{p['odds']:5.2f}" if p["odds"] > 1 else "  n/d "
            print(f"    {ic} {p['date']} {p['match'][:34]:34s} {p['label'][:24]:24s} "
                  f"{cote} {st_txt}")


def main(argv: list[str]) -> None:
    cmd = argv[1] if len(argv) > 1 else "report"
    {"init": cmd_init, "add": cmd_add, "settle": cmd_settle,
     "pending": cmd_pending, "report": cmd_report}.get(cmd, cmd_report)(argv)


if __name__ == "__main__":
    main(sys.argv)
