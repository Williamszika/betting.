import { supabase } from '@/lib/supabase';
import type { Coupon, RecordSummary, Status } from '@/lib/types';

export const dynamic = 'force-dynamic';   // toujours frais
export const revalidate = 0;

const LABEL: Record<Status, string> = { won: 'GAGNÉ', lost: 'PERDU', void: 'VOID', pending: 'EN ATTENTE' };
const pct = (x: number) => `${Math.round(x * 100)}%`;

function Summary({ r }: { r: RecordSummary }) {
  const settled = r.won + r.lost;
  const winRate = settled ? r.won / settled : 0;
  const roi = r.staked ? r.profit / r.staked : 0;
  return (
    <div className="kpis">
      <div className="kpi"><b style={{ color: 'var(--won)' }}>{r.won}</b><span>gagnés</span></div>
      <div className="kpi"><b style={{ color: 'var(--lost)' }}>{r.lost}</b><span>perdus</span></div>
      <div className="kpi"><b>{r.pending}</b><span>en attente</span></div>
      <div className="kpi"><b>{pct(winRate)}</b><span>réussite</span></div>
      <div className="kpi"><b style={{ color: roi >= 0 ? 'var(--won)' : 'var(--lost)' }}>{roi >= 0 ? '+' : ''}{pct(roi)}</b><span>ROI</span></div>
      <div className="kpi"><b>{r.profit >= 0 ? '+' : ''}{r.profit.toFixed(2)}</b><span>profit (u)</span></div>
    </div>
  );
}

function CouponCard({ c }: { c: Coupon }) {
  return (
    <div className={`card ${c.status}`}>
      <div className="head">
        <span className={`badge ${c.status}`}>{LABEL[c.status]}</span>
        <b>{c.id}</b>
        <span className="muted">cote {Number(c.total_odds ?? 0).toFixed(2)} · proba est. {pct(Number(c.joint_prob ?? 0))}
          {c.out_of_range ? ' · (hors fourchette)' : ''}</span>
      </div>
      {(c.coupon_legs ?? []).map((l) => (
        <div className="leg" key={l.id}>
          <span className={`dot ${l.result}`} />
          <span>{l.match} — <b>{l.pick}</b> <span className="mk">({l.market})</span> @ {Number(l.odds ?? 0).toFixed(2)}</span>
        </div>
      ))}
      {c.retro?.what_happened && (
        <div className="retro">🧠 <b>Rétro :</b> {c.retro.what_happened}
          {c.retro.features_to_add?.length ? (
            <ul style={{ margin: '.3rem 0 0 1rem' }}>{c.retro.features_to_add.map((f, i) => <li key={i}>➕ {f}</li>)}</ul>
          ) : null}
        </div>
      )}
    </div>
  );
}

export default async function Home() {
  const sb = supabase();
  if (!sb) {
    return (
      <main className="wrap">
        <h1>📊 SportPredix — Suivi</h1>
        <div className="notice">
          <b>Base non configurée.</b> Renseigne <code>NEXT_PUBLIC_SUPABASE_URL</code> et
          {' '}<code>NEXT_PUBLIC_SUPABASE_ANON_KEY</code> (voir <code>web/.env.example</code>),
          applique la migration <code>supabase/migrations/0001_init.sql</code>, puis recharge.
        </div>
      </main>
    );
  }

  const { data: coupons } = await sb
    .from('coupons')
    .select('*, coupon_legs(*)')
    .order('match_date', { ascending: false })
    .limit(60);
  const { data: rec } = await sb.from('record_summary').select('*').single();

  const summary: RecordSummary = (rec as RecordSummary) ?? { total: 0, won: 0, lost: 0, pending: 0, staked: 0, profit: 0 };

  return (
    <main className="wrap">
      <h1>📊 SportPredix — Suivi des coupons</h1>
      <div className="sub">🟢 gagné · 🔴 perdu · ROI réel dans le temps — le seul juge de la performance.</div>
      <Summary r={summary} />
      {(coupons as Coupon[] | null)?.length
        ? (coupons as Coupon[]).map((c) => <CouponCard key={c.id} c={c} />)
        : <div className="notice">Aucun coupon enregistré. Le job quotidien (Claude Code) pousse les coupons dans Supabase via <code>scripts/push_to_supabase.py</code>.</div>}
      <div className="disc">ESTIMATIONS statistiques, PAS des certitudes. Aucun pari n'est « sûr ». Jeu responsable — joueurs-info-service.fr, 09 74 75 13 13.</div>
    </main>
  );
}
