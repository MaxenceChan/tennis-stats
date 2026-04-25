import { useEffect, useState } from "react";
import { api, type TournamentBase } from "../api/client";
import { surfaceChipClass, surfaceLabel, categoryChipClass } from "../lib/surface";

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
      <div className="page-head">
        <h1>Calendrier ATP {year}</h1>
        <p className="sub">{rows.length} tournoi{rows.length > 1 ? "s" : ""} référencés.</p>
      </div>
      <div className="toolbar">
        <label>
          Année
          <input
            type="number"
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            min={2000}
            max={2030}
            style={{ width: 90 }}
          />
        </label>
        <label>
          Catégorie
          <select value={category} onChange={(e) => setCategory(e.target.value)}>
            <option value="">Toutes</option>
            {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </label>
      </div>
      {err && <p className="error">{err}</p>}
      <div className="table-wrap">
        <table className="data-table">
          <thead>
            <tr>
              <th style={{ width: 110 }}>Date</th>
              <th>Tournoi</th>
              <th style={{ width: 130 }}>Catégorie</th>
              <th style={{ width: 100 }}>Surface</th>
              <th>Lieu</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((t) => (
              <tr key={t.id}>
                <td style={{ color: "var(--muted)", fontFamily: "var(--font-mono)", fontSize: "0.85rem" }}>
                  {fmtDate(t.start_date)}
                </td>
                <td style={{ fontWeight: 500 }}>{t.name}</td>
                <td>
                  {t.category ? (
                    <span className={categoryChipClass(t.category)}>{t.category}</span>
                  ) : "—"}
                </td>
                <td>
                  <span className={surfaceChipClass(t.surface)}>
                    <span className="chip-dot" />
                    {surfaceLabel(t.surface)}
                  </span>
                </td>
                <td style={{ color: "var(--muted)" }}>
                  {[t.city, t.country].filter(Boolean).join(", ") || "—"}
                </td>
              </tr>
            ))}
            {!loading && rows.length === 0 && (
              <tr><td colSpan={5} className="empty">Aucun tournoi pour ces filtres.</td></tr>
            )}
            {loading && (
              <tr><td colSpan={5} className="empty">Chargement…</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </>
  );
}

function fmtDate(s: string | null): string {
  if (!s) return "—";
  try {
    const d = new Date(s);
    return d.toLocaleDateString("fr-FR", { day: "2-digit", month: "short" });
  } catch {
    return s;
  }
}
