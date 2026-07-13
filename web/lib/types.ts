export type Status = 'pending' | 'won' | 'lost' | 'void';

export type Leg = {
  id: number;
  coupon_id: string;
  match: string | null;
  sport: string | null;
  competition: string | null;
  market: string | null;
  pick: string | null;
  odds: number | null;
  est_prob: number | null;
  reliability: number | null;
  result: Status;
  note: string | null;
};

export type Coupon = {
  id: string;
  created_at: string;
  match_date: string | null;
  bookmaker: string | null;
  total_odds: number | null;
  joint_prob: number | null;
  stake: number | null;
  status: Status;
  out_of_range: boolean | null;
  settled_at: string | null;
  retro: { what_happened?: string; features_to_add?: string[] } | null;
  coupon_legs?: Leg[];
};

export type RecordSummary = {
  total: number; won: number; lost: number; pending: number;
  staked: number; profit: number;
};
