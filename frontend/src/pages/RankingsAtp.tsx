import { useEffect, useState } from "react";
import { api, type RankingRow } from "../api/client";
import RankingTable from "../components/RankingTable";

export default function RankingsAtp() {
  const [rows, setRows] = useState<RankingRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.rankings.atp(200)
      .then(setRows)
      .catch((e) => setErr(String(e)))
      .finally(() => setLoading(false));
  }, []);

  return (
    <>
      <div className="page-head">
        <h1>Classement ATP</h1>
        <p className="sub">Top 200 mondial — mis à jour chaque lundi.</p>
      </div>
      {loading && <SkeletonTable />}
      {err && <p className="error">{err}</p>}
      {!loading && !err && <RankingTable rows={rows} pointsLabel="Points ATP" />}
    </>
  );
}

function SkeletonTable() {
  return (
    <div className="table-wrap" style={{ padding: 16 }}>
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className="skeleton skeleton-row" />
      ))}
    </div>
  );
}
