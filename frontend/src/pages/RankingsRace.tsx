import { useEffect, useState } from "react";
import { api, type RankingRow } from "../api/client";
import RankingTable from "../components/RankingTable";

export default function RankingsRace() {
  const [rows, setRows] = useState<RankingRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.rankings.race(200)
      .then(setRows)
      .catch((e) => setErr(String(e)))
      .finally(() => setLoading(false));
  }, []);

  return (
    <>
      <div className="page-head">
        <h1>ATP Race to Turin</h1>
        <p className="sub">
          Classement de la saison en cours — les 8 premiers se qualifient pour les
          Nitto ATP Finals à Turin.
        </p>
      </div>
      {loading && <p>Chargement…</p>}
      {err && <p className="error">{err}</p>}
      {!loading && !err && <RankingTable rows={rows} pointsLabel="Points Race" />}
    </>
  );
}
