import { Link } from "react-router-dom";
import type { RankingRow } from "../api/client";
import { flagEmoji } from "../lib/flag";

type Props = {
  rows: RankingRow[];
  pointsLabel?: string;
  showPodium?: boolean;
};

export default function RankingTable({ rows, pointsLabel = "Points", showPodium = true }: Props) {
  const top3 = showPodium ? rows.slice(0, 3) : [];
  const rest = showPodium ? rows.slice(3) : rows;

  return (
    <>
      {top3.length === 3 && <Podium rows={top3} pointsLabel={pointsLabel} />}

      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th style={{ width: 60 }}>Rang</th>
              <th style={{ width: 50 }}></th>
              <th>Joueur</th>
              <th className="num">{pointsLabel}</th>
            </tr>
          </thead>
          <tbody>
            {rest.map((r) => (
              <tr key={r.player_id}>
                <td className="num" style={{ color: "var(--muted)" }}>{r.rank}</td>
                <td>
                  <span className="flag" title={r.country ?? ""}>
                    {flagEmoji(r.country) || <span className="country-code">{r.country ?? ""}</span>}
                  </span>
                </td>
                <td>
                  <Link to={`/players/${r.player_id}`} className="player-link">
                    {r.player_name}
                  </Link>
                </td>
                <td className="num">{r.points?.toLocaleString("fr-FR") ?? "—"}</td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={4} className="empty">Aucune donnée pour le moment.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}

function Podium({ rows, pointsLabel }: { rows: RankingRow[]; pointsLabel: string }) {
  // Order: 2 — 1 — 3 (silver / gold / bronze) for podium feel
  const [first, second, third] = rows;
  const ordered = [
    { row: second, cls: "silver", label: "#2" },
    { row: first,  cls: "gold",   label: "#1" },
    { row: third,  cls: "bronze", label: "#3" },
  ];

  return (
    <div className="podium">
      {ordered.map(({ row, cls, label }) => (
        <Link key={row.player_id} to={`/players/${row.player_id}`} className={`podium-card ${cls}`}>
          <div className="podium-rank">{label}</div>
          <div className="podium-name">{row.player_name}</div>
          <div className="podium-meta">
            <span className="flag">{flagEmoji(row.country)}</span>
            <span className="country-code">{row.country ?? ""}</span>
          </div>
          <div className="podium-points">
            {row.points?.toLocaleString("fr-FR") ?? "—"} <span style={{ color: "var(--muted)", fontSize: "0.78rem", fontWeight: 500 }}>{pointsLabel}</span>
          </div>
        </Link>
      ))}
    </div>
  );
}
