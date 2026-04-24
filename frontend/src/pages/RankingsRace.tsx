import { useEffect, useState } from "react";
import { api, type RankingRow } from "../api/client";
import RankingTable from "../components/RankingTable";

export default function RankingsRace() {
  const [rows, setRows] = useState<RankingRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.rankings.race(200).then(setRows).catch((e) => setErr(String(e))).finally(() => setLoading(false));
  }, []);

  return (
    <>
      <h1>Classement ATP Race Live</h1>
      {loading && <p>Chargement…</p>}
      {err && <p className="error">{err}</p>}
      {!loading && !err && <RankingTable rows={rows} pointsLabel="Points Race" />}
    </>
  );
}
