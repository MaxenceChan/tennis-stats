import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type PlayerBase } from "../api/client";
import { flagEmoji } from "../lib/flag";

export default function PlayerSearch() {
  const [q, setQ] = useState("");
  const [rows, setRows] = useState<PlayerBase[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!q) { setRows([]); return; }
    const t = setTimeout(() => {
      setLoading(true);
      api.players.search(q, 20)
        .then(setRows)
        .catch(() => setRows([]))
        .finally(() => setLoading(false));
    }, 200);
    return () => clearTimeout(t);
  }, [q]);

  return (
    <>
      <div className="page-head">
        <h1>Rechercher un joueur</h1>
        <p className="sub">Tape un nom ou prénom — 65 000 joueurs ATP indexés.</p>
      </div>
      <div className="search-wrap">
        <input
          className="search"
          placeholder="Alcaraz, Sinner, Djokovic, Federer…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          autoFocus
        />
      </div>
      {loading && <p style={{ color: "var(--muted)", marginTop: "1rem" }}>Recherche…</p>}
      {!loading && q && rows.length === 0 && (
        <p className="empty">Aucun joueur ne correspond à « {q} ».</p>
      )}
      <ul className="search-results">
        {rows.map((p) => (
          <li key={p.id}>
            <Link to={`/players/${p.id}`}>
              <span className="rank">{p.atp_rank ? `#${p.atp_rank}` : "—"}</span>
              <span className="name">
                <span className="flag">{flagEmoji(p.country)}</span>
                {p.full_name}
              </span>
              <span className="meta">
                <span className="country-code">{p.country ?? ""}</span>
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </>
  );
}
