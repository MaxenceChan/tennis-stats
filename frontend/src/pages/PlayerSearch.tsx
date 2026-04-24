import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, type PlayerBase } from "../api/client";

export default function PlayerSearch() {
  const [q, setQ] = useState("");
  const [rows, setRows] = useState<PlayerBase[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!q) { setRows([]); return; }
    const t = setTimeout(() => {
      setLoading(true);
      api.players.search(q, 20).then(setRows).catch(() => setRows([])).finally(() => setLoading(false));
    }, 200);
    return () => clearTimeout(t);
  }, [q]);

  return (
    <>
      <h1>Recherche de joueur</h1>
      <input
        className="search"
        placeholder="Nom ou prénom (ex. Alcaraz, Sinner, Djokovic…)"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        autoFocus
      />
      {loading && <p>Recherche…</p>}
      <ul className="search-results">
        {rows.map((p) => (
          <li key={p.id}>
            <Link to={`/players/${p.id}`}>
              <span className="rank">#{p.atp_rank ?? "—"}</span>
              <span className="name">{p.full_name}</span>
              <span className="meta">{p.country ?? ""}</span>
            </Link>
          </li>
        ))}
      </ul>
    </>
  );
}
