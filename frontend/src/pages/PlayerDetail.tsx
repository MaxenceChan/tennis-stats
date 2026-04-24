import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api, type MatchRead, type PlayerFullProfile } from "../api/client";

export default function PlayerDetail() {
  const { playerId } = useParams<{ playerId: string }>();
  const [profile, setProfile] = useState<PlayerFullProfile | null>(null);
  const [tab, setTab] = useState<"recent" | "all" | "seasons" | "titles" | "events">("recent");
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

  if (loading) return <p>Chargement…</p>;
  if (err) return <p className="error">{err}</p>;
  if (!profile) return <p>Joueur introuvable.</p>;

  const p = profile.player;

  return (
    <>
      <header className="player-header">
        <div>
          <h1>{p.full_name}</h1>
          <div className="player-meta">
            <span>Pays : {p.country ?? "—"}</span>
            <span>Âge : {p.age ?? "—"}</span>
            <span>Taille : {p.height_cm ? `${p.height_cm} cm` : "—"}</span>
            <span>Poids : {p.weight_kg ? `${p.weight_kg} kg` : "—"}</span>
            <span>Main : {p.hand ?? "—"}</span>
          </div>
          <div className="player-meta">
            <span>ATP : <strong>#{p.atp_rank ?? "—"}</strong></span>
            <span>Race : <strong>#{p.race_rank ?? "—"}</strong></span>
            <span>Elo : <strong>{p.elo_rating ? p.elo_rating.toFixed(1) : "—"}</strong></span>
          </div>
          <div className="player-links">
            {p.tennis_abstract_url && <a href={p.tennis_abstract_url} target="_blank" rel="noreferrer">Tennis Abstract ↗</a>}
            {p.wikipedia_url && <a href={p.wikipedia_url} target="_blank" rel="noreferrer">Wikipedia ↗</a>}
          </div>
        </div>
      </header>

      <nav className="tabs">
        <button className={tab === "recent" ? "active" : ""} onClick={() => setTab("recent")}>Recent Results</button>
        <button className={tab === "all" ? "active" : ""} onClick={() => setTab("all")}>All Results</button>
        <button className={tab === "seasons" ? "active" : ""} onClick={() => setTab("seasons")}>Tour-Level Seasons</button>
        <button className={tab === "titles" ? "active" : ""} onClick={() => setTab("titles")}>Titles & Finals</button>
        <button className={tab === "events" ? "active" : ""} onClick={() => setTab("events")}>Major & Recent Events</button>
      </nav>

      {tab === "recent" && <MatchTable matches={profile.recent_results} viewpointId={p.id} />}
      {tab === "all" && <MatchTable matches={profile.all_results} viewpointId={p.id} />}
      {tab === "seasons" && (
        <table className="data-table">
          <thead><tr><th>Année</th><th>V</th><th>D</th><th>Titres</th><th>Finales</th></tr></thead>
          <tbody>
            {profile.tour_level_seasons.map((s) => (
              <tr key={s.year}><td>{s.year}</td><td>{s.wins}</td><td>{s.losses}</td><td>{s.titles}</td><td>{s.finals}</td></tr>
            ))}
          </tbody>
        </table>
      )}
      {tab === "titles" && (
        <table className="data-table">
          <thead><tr><th>Année</th><th>Tournoi</th><th>Résultat</th></tr></thead>
          <tbody>
            {profile.recent_titles_finals.map((t, i) => (
              <tr key={i}><td>{t.year}</td><td>{t.tournament}</td><td>{t.result}</td></tr>
            ))}
          </tbody>
        </table>
      )}
      {tab === "events" && (
        <table className="data-table">
          <thead><tr><th>Année</th><th>Tournoi</th><th>Tour</th><th>Résultat</th><th>Score</th></tr></thead>
          <tbody>
            {profile.major_recent_events.map((e, i) => (
              <tr key={i}>
                <td>{e.year}</td><td>{e.tournament}</td><td>{e.round ?? "—"}</td>
                <td>{e.result}</td><td>{e.score ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}


function MatchTable({ matches, viewpointId }: { matches: MatchRead[]; viewpointId: number }) {
  if (!matches.length) return <p className="empty">Aucun match en base.</p>;
  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>Date</th><th>Tournoi</th><th>Surf.</th><th>Tour</th>
          <th>Adversaire</th><th>Résultat</th><th>Score</th>
        </tr>
      </thead>
      <tbody>
        {matches.map((m) => {
          const opp = m.player1.id === viewpointId ? m.player2 : m.player1;
          const won = m.winner_id === viewpointId;
          return (
            <tr key={m.id}>
              <td>{m.match_date ?? "—"}</td>
              <td>{m.tournament.name} {m.tournament.year}</td>
              <td>{m.tournament.surface ?? "—"}</td>
              <td>{m.round ?? "—"}</td>
              <td><Link to={`/players/${opp.id}`}>{opp.full_name}</Link></td>
              <td className={won ? "win" : "loss"}>{won ? "V" : "D"}</td>
              <td>{m.score ?? "—"}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
