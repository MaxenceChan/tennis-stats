import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, type MatchRead, type PlayerFullProfile } from "../api/client";
import { flagEmoji } from "../lib/flag";
import { surfaceChipClass, surfaceLabel } from "../lib/surface";

type Tab = "summary" | "all" | "seasons" | "titles" | "events";

const SLAMS: { key: string; label: string; aliases: string[] }[] = [
  { key: "ao",  label: "Australian Open", aliases: ["australian open"] },
  { key: "rg",  label: "Roland-Garros",   aliases: ["roland garros", "french open", "roland-garros"] },
  { key: "wim", label: "Wimbledon",       aliases: ["wimbledon"] },
  { key: "uso", label: "US Open",         aliases: ["us open", "u.s. open"] },
];

const ROUND_RANK: Record<string, number> = {
  "W": 8, "F": 7, "SF": 6, "QF": 5, "R16": 4, "R32": 3, "R64": 2, "R128": 1,
};
const ROUND_LABEL: Record<string, string> = {
  "W": "Vainqueur", "F": "Finale", "SF": "1/2", "QF": "1/4",
  "R16": "1/8", "R32": "3T", "R64": "2T", "R128": "1T",
};

export default function PlayerDetail() {
  const { playerId } = useParams<{ playerId: string }>();
  const [profile, setProfile] = useState<PlayerFullProfile | null>(null);
  const [tab, setTab] = useState<Tab>("summary");
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    if (!playerId) return;
    setLoading(true);
    api.players.profile(Number(playerId))
      .then(setProfile)
      .catch((e) => setErr(String(e)))
      .finally(() => setLoading(false));
  }, [playerId]);

  if (loading) return <p style={{ color: "var(--muted)" }}>Chargement…</p>;
  if (err) return <p className="error">{err}</p>;
  if (!profile) return <p className="empty">Joueur introuvable.</p>;

  const p = profile.player;
  const initials = (p.first_name?.[0] ?? "") + (p.last_name?.[0] ?? "");

  return (
    <>
      <header className="player-hero">
        <div className="player-hero-top">
          <div className="player-avatar" aria-hidden>{initials || "?"}</div>
          <div className="player-name-block">
            <h1>{p.full_name}</h1>
            <div className="player-flag-line">
              <span className="flag">{flagEmoji(p.country)}</span>
              <span>{p.country ?? "—"}</span>
              {p.age != null && <span>• {p.age} ans</span>}
              {p.hand && <span>• Main {p.hand === "L" ? "gauche" : "droite"}</span>}
            </div>
          </div>
        </div>

        <div className="player-stats-grid">
          <div className="stat">
            <div className="stat-label">ATP</div>
            <div className={`stat-value ${p.atp_rank ? "ball" : "muted"}`}>
              {p.atp_rank ? `#${p.atp_rank}` : "—"}
            </div>
            {p.atp_points != null && (
              <div className="stat-sub">{p.atp_points.toLocaleString("fr-FR")} pts</div>
            )}
          </div>
          <div className="stat">
            <div className="stat-label">Race</div>
            <div className={`stat-value ${p.race_rank ? "" : "muted"}`}>
              {p.race_rank ? `#${p.race_rank}` : "—"}
            </div>
          </div>
          <div className="stat">
            <div className="stat-label">Elo</div>
            <div className={`stat-value ${p.elo_rating ? "" : "muted"}`}>
              {p.elo_rating ? p.elo_rating.toFixed(0) : "—"}
            </div>
          </div>
          <div className="stat">
            <div className="stat-label">Taille</div>
            <div className={`stat-value ${p.height_cm ? "" : "muted"}`}>
              {p.height_cm ? `${p.height_cm}` : "—"}
              {p.height_cm && <span style={{ fontSize: "0.85rem", color: "var(--muted)", marginLeft: 4 }}>cm</span>}
            </div>
          </div>
          <div className="stat">
            <div className="stat-label">Poids</div>
            <div className={`stat-value ${p.weight_kg ? "" : "muted"}`}>
              {p.weight_kg ? `${p.weight_kg}` : "—"}
              {p.weight_kg && <span style={{ fontSize: "0.85rem", color: "var(--muted)", marginLeft: 4 }}>kg</span>}
            </div>
          </div>
        </div>

        {(p.tennis_abstract_url || p.wikipedia_url) && (
          <div className="player-links">
            {p.tennis_abstract_url && (
              <a href={p.tennis_abstract_url} target="_blank" rel="noreferrer">Tennis Abstract ↗</a>
            )}
            {p.wikipedia_url && (
              <a href={p.wikipedia_url} target="_blank" rel="noreferrer">Wikipedia ↗</a>
            )}
          </div>
        )}
      </header>

      <nav className="tabs" role="tablist">
        <Tab id="summary" current={tab} set={setTab}>Résumé</Tab>
        <Tab id="all"     current={tab} set={setTab}>Tous les matchs</Tab>
        <Tab id="seasons" current={tab} set={setTab}>Saisons</Tab>
        <Tab id="titles"  current={tab} set={setTab}>Titres & finales</Tab>
        <Tab id="events"  current={tab} set={setTab}>Grands tournois</Tab>
      </nav>

      {tab === "summary" && <Summary profile={profile} />}
      {tab === "all"    && <MatchTable matches={profile.all_results} viewpointId={p.id} />}
      {tab === "seasons" && (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Année</th>
                <th className="num">V</th>
                <th className="num">D</th>
                <th className="num">Titres</th>
                <th className="num">Finales</th>
              </tr>
            </thead>
            <tbody>
              {profile.tour_level_seasons.map((s) => (
                <tr key={s.year}>
                  <td style={{ fontWeight: 600 }}>{s.year}</td>
                  <td className="num win">{s.wins}</td>
                  <td className="num loss">{s.losses}</td>
                  <td className="num">{s.titles}</td>
                  <td className="num">{s.finals}</td>
                </tr>
              ))}
              {profile.tour_level_seasons.length === 0 && (
                <tr><td colSpan={5} className="empty">Aucune saison enregistrée.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
      {tab === "titles" && (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr><th>Année</th><th>Tournoi</th><th>Résultat</th></tr>
            </thead>
            <tbody>
              {profile.recent_titles_finals.map((t, i) => (
                <tr key={i}>
                  <td>{t.year}</td>
                  <td>{t.tournament}</td>
                  <td className={t.result === "Champion" ? "win" : ""}>{t.result}</td>
                </tr>
              ))}
              {profile.recent_titles_finals.length === 0 && (
                <tr><td colSpan={3} className="empty">Aucun titre ou finale.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
      {tab === "events" && (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Année</th>
                <th>Tournoi</th>
                <th>Tour</th>
                <th>Résultat</th>
                <th>Score</th>
              </tr>
            </thead>
            <tbody>
              {profile.major_recent_events.map((e, i) => (
                <tr key={i}>
                  <td>{e.year}</td>
                  <td>{e.tournament}</td>
                  <td style={{ color: "var(--muted)" }}>{e.round ?? "—"}</td>
                  <td className={e.result === "W" ? "win" : "loss"}>{e.result === "W" ? "Victoire" : "Défaite"}</td>
                  <td style={{ fontFamily: "var(--font-mono)", fontSize: "0.88rem" }}>{e.score ?? "—"}</td>
                </tr>
              ))}
              {profile.major_recent_events.length === 0 && (
                <tr><td colSpan={5} className="empty">Aucun match récent en Grand Chelem / Masters.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}

function Tab({ id, current, set, children }: {
  id: Tab; current: Tab; set: (t: Tab) => void; children: React.ReactNode;
}) {
  return (
    <button
      role="tab"
      aria-selected={current === id}
      className={current === id ? "active" : ""}
      onClick={() => set(id)}
    >
      {children}
    </button>
  );
}

// ============================================================
// Summary tab
// ============================================================
function Summary({ profile }: { profile: PlayerFullProfile }) {
  const pid = profile.player.id;

  const totals = useMemo(() => {
    const titles  = profile.tour_level_seasons.reduce((a, s) => a + (s.titles  ?? 0), 0);
    const finals  = profile.tour_level_seasons.reduce((a, s) => a + (s.finals  ?? 0), 0);
    const wins    = profile.tour_level_seasons.reduce((a, s) => a + (s.wins    ?? 0), 0);
    const losses  = profile.tour_level_seasons.reduce((a, s) => a + (s.losses  ?? 0), 0);
    const total   = wins + losses;
    const winPct  = total ? Math.round((wins / total) * 100) : null;
    return { titles, finals, wins, losses, winPct };
  }, [profile]);

  // Best round at most-recent edition of each Grand Slam
  const slamPerf = useMemo(() => {
    return SLAMS.map((slam) => {
      const slamMatches = profile.all_results.filter((m) => {
        const name = (m.tournament.name ?? "").toLowerCase();
        return slam.aliases.some((a) => name.includes(a));
      });
      if (!slamMatches.length) return { ...slam, year: null, round: null, won: false };
      // group by year, keep the most recent
      const byYear = new Map<number, MatchRead[]>();
      for (const m of slamMatches) {
        const y = m.tournament.year;
        if (!byYear.has(y)) byYear.set(y, []);
        byYear.get(y)!.push(m);
      }
      const latestYear = Math.max(...byYear.keys());
      const ms = byYear.get(latestYear)!;
      // best round reached: max ROUND_RANK; if final and player won → "W"
      let bestRound: string | null = null;
      let bestRank = -1;
      let won = false;
      for (const m of ms) {
        const r = m.round ?? "";
        const rank = ROUND_RANK[r] ?? 0;
        if (rank > bestRank) {
          bestRank = rank;
          bestRound = r;
          won = false;
        }
      }
      // if best round is "F" and player won → champion
      if (bestRound === "F") {
        const finalMatch = ms.find((m) => m.round === "F");
        if (finalMatch && finalMatch.winner_id === pid) {
          bestRound = "W";
          won = true;
        }
      } else {
        // they LOST in bestRound (i.e. eliminated there)
        won = false;
      }
      return { ...slam, year: latestYear, round: bestRound, won };
    });
  }, [profile, pid]);

  // Year-end rank progression: for each year, the rank from the latest match of that year
  // where this player has a known rank.
  const rankSeries = useMemo(() => {
    // sort ascending by date
    const sorted = [...profile.all_results]
      .filter((m) => m.match_date)
      .sort((a, b) => (a.match_date! < b.match_date! ? -1 : 1));
    const byYear = new Map<number, number>(); // year → last rank seen
    for (const m of sorted) {
      const y = new Date(m.match_date!).getFullYear();
      const myRank = m.player1.id === pid ? m.atp_rank_p1 : m.atp_rank_p2;
      if (myRank != null && myRank > 0) byYear.set(y, myRank);
    }
    return Array.from(byYear.entries())
      .map(([year, rank]) => ({ year, rank }))
      .sort((a, b) => a.year - b.year);
  }, [profile, pid]);

  return (
    <div className="summary">
      {/* --- Top stat cards --- */}
      <div className="summary-stats">
        <SummaryCard label="Titres"   value={totals.titles}  accent="ball" />
        <SummaryCard label="Finales"  value={totals.finals} />
        <SummaryCard label="Victoires" value={totals.wins}   accent="win" />
        <SummaryCard label="Défaites" value={totals.losses}  accent="loss" />
        <SummaryCard label="% Victoires" value={totals.winPct != null ? `${totals.winPct}%` : "—"} />
      </div>

      {/* --- Grand Slam performance --- */}
      <section className="summary-section">
        <h2 className="summary-h2">Grand Chelem — dernière édition</h2>
        <div className="slams-grid">
          {slamPerf.map((s) => (
            <div key={s.key} className={`slam-card ${s.won ? "champion" : ""}`}>
              <div className="slam-name">{s.label}</div>
              <div className="slam-round">
                {s.round ? (ROUND_LABEL[s.round] ?? s.round) : "—"}
              </div>
              <div className="slam-year">{s.year ?? "Aucune participation"}</div>
            </div>
          ))}
        </div>
      </section>

      {/* --- Rank progression chart --- */}
      <section className="summary-section">
        <h2 className="summary-h2">Progression classement ATP (fin d'année)</h2>
        {rankSeries.length >= 2 ? (
          <RankChart data={rankSeries} />
        ) : (
          <p className="empty">Pas assez de données de classement.</p>
        )}
      </section>
    </div>
  );
}

function SummaryCard({ label, value, accent }: {
  label: string; value: number | string | null; accent?: "ball" | "win" | "loss";
}) {
  return (
    <div className="summary-card">
      <div className="summary-card-label">{label}</div>
      <div className={`summary-card-value ${accent ?? ""}`}>{value ?? "—"}</div>
    </div>
  );
}

// ============================================================
// SVG Rank Chart — full-width, yellow line, data labels
// ============================================================
function RankChart({ data }: { data: { year: number; rank: number }[] }) {
  const W = 1000;
  const H = 320;
  const PAD_L = 50;
  const PAD_R = 30;
  const PAD_T = 40;
  const PAD_B = 50;
  const innerW = W - PAD_L - PAD_R;
  const innerH = H - PAD_T - PAD_B;

  const minYear = data[0].year;
  const maxYear = data[data.length - 1].year;
  const yearSpan = Math.max(1, maxYear - minYear);

  const ranks = data.map((d) => d.rank);
  const minRank = 1; // best
  const maxRank = Math.max(...ranks, 10);

  const x = (year: number) => PAD_L + ((year - minYear) / yearSpan) * innerW;
  // invert Y so rank #1 is at top
  const y = (rank: number) =>
    PAD_T + ((rank - minRank) / Math.max(1, maxRank - minRank)) * innerH;

  const pathD = data.map((d, i) => `${i === 0 ? "M" : "L"} ${x(d.year)} ${y(d.rank)}`).join(" ");

  // Y gridlines: 1, then nice values up to maxRank
  const niceTicks = (() => {
    const ticks = [1];
    const candidates = [5, 10, 25, 50, 100, 200, 500, 1000];
    for (const c of candidates) if (c <= maxRank) ticks.push(c);
    if (ticks[ticks.length - 1] !== maxRank) ticks.push(maxRank);
    return Array.from(new Set(ticks));
  })();

  return (
    <div className="chart-wrap">
      <svg viewBox={`0 0 ${W} ${H}`} className="rank-chart" role="img" aria-label="Progression classement ATP">
        <defs>
          <linearGradient id="rankFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%"   stopColor="#d8e84a" stopOpacity="0.35" />
            <stop offset="100%" stopColor="#d8e84a" stopOpacity="0" />
          </linearGradient>
        </defs>

        {/* Y gridlines + labels */}
        {niceTicks.map((t) => (
          <g key={t}>
            <line
              x1={PAD_L} x2={W - PAD_R}
              y1={y(t)} y2={y(t)}
              stroke="#252a36" strokeDasharray="3 4"
            />
            <text
              x={PAD_L - 10} y={y(t) + 4}
              fill="#8993a8" fontSize="11" textAnchor="end"
              fontFamily="var(--font-mono)"
            >
              #{t}
            </text>
          </g>
        ))}

        {/* X axis labels */}
        {data.map((d) => (
          <text
            key={`xl-${d.year}`}
            x={x(d.year)} y={H - PAD_B + 22}
            fill="#8993a8" fontSize="11" textAnchor="middle"
            fontFamily="var(--font-mono)"
          >
            {d.year}
          </text>
        ))}

        {/* Filled area below the line */}
        <path
          d={`${pathD} L ${x(maxYear)} ${H - PAD_B} L ${x(minYear)} ${H - PAD_B} Z`}
          fill="url(#rankFill)"
        />

        {/* Line */}
        <path
          d={pathD}
          fill="none"
          stroke="#d8e84a"
          strokeWidth="2.5"
          strokeLinejoin="round"
          strokeLinecap="round"
        />

        {/* Points + data labels */}
        {data.map((d) => (
          <g key={`pt-${d.year}`}>
            <circle cx={x(d.year)} cy={y(d.rank)} r="4.5" fill="#0a0c14" stroke="#d8e84a" strokeWidth="2" />
            <rect
              x={x(d.year) - 22}
              y={y(d.rank) - 28}
              width="44" height="20" rx="4"
              fill="#13161f" stroke="#d8e84a" strokeOpacity="0.35"
            />
            <text
              x={x(d.year)} y={y(d.rank) - 14}
              fill="#d8e84a" fontSize="12" fontWeight="700"
              textAnchor="middle" fontFamily="var(--font-mono)"
            >
              #{d.rank}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}

function MatchTable({ matches, viewpointId }: { matches: MatchRead[]; viewpointId: number }) {
  if (!matches.length) return <p className="empty">Aucun match en base.</p>;
  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            <th style={{ width: 110 }}>Date</th>
            <th>Tournoi</th>
            <th style={{ width: 110 }}>Surface</th>
            <th style={{ width: 60 }}>Tour</th>
            <th>Adversaire</th>
            <th style={{ width: 90 }}>Résultat</th>
            <th>Score</th>
          </tr>
        </thead>
        <tbody>
          {matches.map((m) => {
            const opp = m.player1.id === viewpointId ? m.player2 : m.player1;
            const won = m.winner_id === viewpointId;
            return (
              <tr key={m.id}>
                <td style={{ color: "var(--muted)", fontFamily: "var(--font-mono)", fontSize: "0.85rem" }}>
                  {m.match_date ?? "—"}
                </td>
                <td>{m.tournament.name} <span style={{ color: "var(--faint)" }}>{m.tournament.year}</span></td>
                <td>
                  <span className={surfaceChipClass(m.tournament.surface)}>
                    {surfaceLabel(m.tournament.surface)}
                  </span>
                </td>
                <td style={{ color: "var(--muted)", fontFamily: "var(--font-mono)", fontSize: "0.82rem" }}>
                  {m.round ?? "—"}
                </td>
                <td>
                  <Link to={`/players/${opp.id}`} className="player-link">
                    <span className="flag">{flagEmoji(opp.country)}</span>
                    {opp.full_name}
                  </Link>
                </td>
                <td className={won ? "win" : "loss"}>{won ? "Victoire" : "Défaite"}</td>
                <td style={{ fontFamily: "var(--font-mono)", fontSize: "0.88rem" }}>
                  {m.score ?? "—"}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
