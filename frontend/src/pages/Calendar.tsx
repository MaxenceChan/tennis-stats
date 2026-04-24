import { useEffect, useState } from "react";
import { api, type TournamentBase } from "../api/client";

const CATEGORIES = ["Grand Slam", "Masters 1000", "ATP 500", "ATP 250", "ATP Finals"];

export default function Calendar() {
  const [rows, setRows] = useState<TournamentBase[]>([]);
  const [year, setYear] = useState<number>(new Date().getFullYear());
  const [category, setCategory] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    api.calendar(year, category || undefined)
      .then(setRows)
      .catch((e) => setErr(String(e)))
      .finally(() => setLoading(false));
  }, [year, category]);

  return (
    <>
      <h1>Calendrier ATP {year}</h1>
      <div className="toolbar">
        <label>
          Année :{" "}
          <input
            type="number"
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            min={2000}
            max={2030}
          />
        </label>
        <label>
          Catégorie :{" "}
          <select value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="">Toutes</option>
            {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </label>
      </div>
      {loading && <p>Chargement…</p>}
      {err && <p className="error">{err}</p>}
      <table className="data-table">
        <thead>
          <tr>
            <th>Semaine</th>
            <th>Tournoi</th>
            <th>Catégorie</th>
            <th>Surface</th>
            <th>Lieu</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((t) => (
            <tr key={t.id}>
              <td>{t.start_date ?? "—"}</td>
              <td>{t.name}</td>
              <td>{t.category ?? "—"}</td>
              <td>{t.surface ?? "—"}</td>
              <td>{[t.city, t.country].filter(Boolean).join(", ") || "—"}</td>
            </tr>
          ))}
          {!loading && rows.length === 0 && (
            <tr><td colSpan={5} className="empty">Aucun tournoi.</td></tr>
          )}
        </tbody>
      </table>
    </>
  );
}
