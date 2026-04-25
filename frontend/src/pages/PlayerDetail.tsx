import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, type MatchRead, type PlayerFullProfile } from "../api/client";
import { flagEmoji } from "../lib/flag";
import { surfaceChipClass, surfaceLabel } from "../lib/surface";

type Tab = "recent" | "all" | "seasons" | "titles" | "events";

export default function PlayerDetail() {
  const { playerId } = useParams<{ playerId: string }>();
  const [profile, setProfile] = useState<PlayerFullProfile | null>(null);
  const [tab, setTab] = useState<Tab>("recent");
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
        <Tab id="recent"  current={tab} set={setTab}>Résultats récents</Tab>
        <Tab id="all"     current={tab} set={setTab}>Tous les matchs</Tab>
        <Tab id="seasons" current={tab} set={setTab}>Saisons</Tab>
        <Tab id="titles"  current={tab} set={setTab}>Titres & finales</Tab>
        <Tab id="events"  current={tab} set={setTab}>Grands tournois</Tab>
      </nav>

      {tab === "recent" && <MatchTable matches={profile.recent_results} viewpointId={p.id} />}
      {tab === "all"    && <MatchTable matches={profile.all_results}    viewpointId={p.id} />}
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
