import { useEffect, useState } from "react";
import { api, type RankingRow } from "../api/client";
import RankingTable from "../components/RankingTable";

const SURFACES = [
  { value: "all", label: "Toutes surfaces" },
  { value: "Hard", label: "Dur" },
  { value: "Clay", label: "Terre battue" },
  { value: "Grass", label: "Gazon" },
];

export default function RankingsElo() {
  const [rows, setRows] = useState<RankingRow[]>([]);
  const [surface, setSurface] = useState("all");
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setErr(null);
    api.rankings.elo(200, surface)
      .then(setRows)
      .catch((e) => setErr(String(e)))
      .finally(() => setLoading(false));
  }, [surface]);

  return (
    <>
      <h1>Classement Elo</h1>
      <div className="toolbar">
        <label>
          Surface :{" "}
          <select value={surface} onChange={(e) => setSurface(e.target.value)}>
            {SURFACES.map((s) => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
        </label>
      </div>
      {loading && <p>Chargement…</p>}
      {err && <p className="error">{err}</p>}
      {!loading && !err && <RankingTable rows={rows} pointsLabel="Elo" />}
    </>
  );
}
