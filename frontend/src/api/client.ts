const BASE = (import.meta.env.VITE_API_BASE_URL as string) || "http://localhost:8000/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!r.ok) {
    const txt = await r.text().catch(() => "");
    throw new Error(`API ${r.status} ${r.statusText}: ${txt}`);
  }
  return r.json() as Promise<T>;
}

export const api = {
  rankings: {
    atp: (limit = 100) => request<RankingRow[]>(`/rankings/atp?limit=${limit}`),
    race: (limit = 100) => request<RankingRow[]>(`/rankings/race?limit=${limit}`),
    elo: (limit = 100, surface = "all") =>
      request<RankingRow[]>(`/rankings/elo?limit=${limit}&surface=${surface}`),
  },
  players: {
    search: (q: string, limit = 20) =>
      request<PlayerBase[]>(`/players/search?q=${encodeURIComponent(q)}&limit=${limit}`),
    detail: (id: number) => request<PlayerDetail>(`/players/${id}`),
    profile: (id: number) => request<PlayerFullProfile>(`/players/${id}/profile`),
    matches: (id: number, limit = 50) =>
      request<MatchRead[]>(`/players/${id}/matches?limit=${limit}`),
  },
  calendar: (year?: number, category?: string) => {
    const qs = new URLSearchParams();
    if (year) qs.set("year", String(year));
    if (category) qs.set("category", category);
    const s = qs.toString();
    return request<TournamentWithWinner[]>(`/calendar${s ? `?${s}` : ""}`);
  },
};

// ---------------- types --------------------
export type RankingRow = {
  rank: number;
  player_id: number;
  player_name: string;
  country: string | null;
  points: number | null;
};

export type PlayerBase = {
  id: number;
  slug: string;
  full_name: string;
  country: string | null;
  atp_rank: number | null;
  race_rank: number | null;
  elo_rating: number | null;
};

export type PlayerDetail = PlayerBase & {
  first_name: string | null;
  last_name: string | null;
  birth_date: string | null;
  age: number | null;
  height_cm: number | null;
  weight_kg: number | null;
  hand: string | null;
  backhand: string | null;
  atp_points: number | null;
  race_points: number | null;
  wikipedia_url: string | null;
  tennis_abstract_url: string | null;
};

export type TournamentBase = {
  id: number;
  slug: string;
  name: string;
  year: number;
  surface: string | null;
  category: string | null;
  city: string | null;
  country: string | null;
  start_date: string | null;
  end_date: string | null;
  draw_size: number | null;
};

export type TournamentWithWinner = TournamentBase & {
  winner: PlayerBase | null;
};

export type MatchStats = {
  first_serve_pct: number | null;
  first_serve_win_pct: number | null;
  second_serve_win_pct: number | null;
  break_points_saved: number | null;
  double_fault_pct: number | null;
  dominance_ratio: number | null;
  ace_pct: number | null;
};

export type MatchRead = {
  id: number;
  match_date: string | null;
  round: string | null;
  score: string | null;
  sets_count: number | null;
  duration_minutes: number | null;
  tournament: TournamentBase;
  player1: PlayerBase;
  player2: PlayerBase;
  winner_id: number | null;
  loser_id: number | null;
  atp_rank_p1: number | null;
  atp_rank_p2: number | null;
  stats_p1: MatchStats | null;
  stats_p2: MatchStats | null;
};

export type SeasonRow = {
  year: number;
  wins: number;
  losses: number;
  titles: number;
  finals: number;
  year_end_rank?: number | null;
};

export type PlayerFullProfile = {
  player: PlayerDetail;
  recent_results: MatchRead[];
  all_results: MatchRead[];
  tour_level_seasons: SeasonRow[];
  recent_titles_finals: Array<{
    year: number;
    tournament: string | null;
    result: string;
    opponent_id: number | null;
  }>;
  year_end_rankings: Array<Record<string, unknown>>;
  major_recent_events: Array<{
    tournament: string;
    year: number;
    round: string | null;
    result: string;
    score: string | null;
  }>;
};
