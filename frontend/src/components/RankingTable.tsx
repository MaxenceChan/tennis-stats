import { Link } from "react-router-dom";
import type { RankingRow } from "../api/client";

export default function RankingTable({ rows, pointsLabel = "Points" }: { rows: RankingRow[]; pointsLabel?: string }) {
  return (
    <table className="data-table">
      <thead>
        <tr>
          <th>Rang</th>
          <th>Pays</th>
          <th>Joueur</th>
          <th className="num">{pointsLabel}</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr key={r.player_id}>
            <td className="num">{r.rank}</td>
            <td>{r.country ?? ""}</td>
            <td>
              <Link to={`/players/${r.player_id}`}>{r.player_name}</Link>
            </td>
            <td className="num">{r.points ?? "—"}</td>
          </tr>
        ))}
        {rows.length === 0 && (
          <tr>
            <td colSpan={4} className="empty">Aucune donnée — lancez un scraping côté admin.</td>
          </tr>
        )}
      </tbody>
    </table>
  );
}
