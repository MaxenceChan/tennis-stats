import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { api, type LiveMatch } from "../api/client";
import { flagEmoji } from "../lib/flag";
import { surfaceChipClass, surfaceLabel } from "../lib/surface";

const REFRESH_MS = 60_000;
// Si la dernière maj date d'avant ce seuil, on rafraîchit au retour de l'onglet.
const STALE_AFTER_MS = 30_000;

export default function Live() {
  const [matches, setMatches] = useState<LiveMatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null);

  const cancelledRef = useRef(false);
  const updatedAtRef = useRef<Date | null>(null);
  updatedAtRef.current = updatedAt;

  const load = useCallback(async () => {
    setRefreshing(true);
    try {
      const rows = await api.live.matches();
      if (cancelledRef.current) return;
      setMatches(rows);
      setUpdatedAt(new Date());
      setErr(null);
    } catch (e) {
      if (!cancelledRef.current) setErr(String(e));
    } finally {
      if (!cancelledRef.current) {
        setLoading(false);
        setRefreshing(false);
      }
    }
  }, []);

  useEffect(() => {
    cancelledRef.current = false;
    load();

    let intervalId: number | null = null;
    const startInterval = () => {
      if (intervalId == null) {
        intervalId = window.setInterval(load, REFRESH_MS);
      }
    };
    const stopInterval = () => {
      if (intervalId != null) {
        window.clearInterval(intervalId);
        intervalId = null;
      }
    };

    const onVisibility = () => {
      if (document.hidden) {
        stopInterval();
      } else {
        // Si données vieilles, on rafraîchit immédiatement avant de relancer
        const last = updatedAtRef.current;
        if (!last || Date.now() - last.getTime() > STALE_AFTER_MS) {
          load();
        }
        startInterval();
      }
    };

    if (!document.hidden) startInterval();
    document.addEventListener("visibilitychange", onVisibility);

    return () => {
      cancelledRef.current = true;
      stopInterval();
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [load]);

  const inProgress = useMemo(
    () => matches.filter((m) => m.status === "inprogress"),
    [matches]
  );
  const finished = useMemo(
    () => matches.filter((m) => m.status === "finished"),
    [matches]
  );
  const upcoming = useMemo(
    () => matches.filter((m) => m.status !== "inprogress" && m.status !== "finished"),
    [matches]
  );

  return (
    <>
      <div className="page-head live-head">
        <div>
          <h1>
            <span className="live-dot" aria-hidden /> En direct
          </h1>
          <p className="sub">
            {inProgress.length} match{inProgress.length > 1 ? "s" : ""} en cours
            {updatedAt && ` — actualisé à ${updatedAt.toLocaleTimeString("fr-FR")}`}
          </p>
        </div>
        <button
          type="button"
          className="refresh-btn"
          onClick={load}
          disabled={refreshing}
          aria-label="Rafraîchir maintenant"
          title="Rafraîchir maintenant"
        >
          <svg
            width="14"
            height="14"
            viewBox="0 0 16 16"
            aria-hidden
            className={refreshing ? "spin" : ""}
          >
            <path
              d="M13.5 8a5.5 5.5 0 1 1-1.61-3.89M13.5 2.5v3h-3"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          {refreshing ? "Actualisation…" : "Rafraîchir"}
        </button>
      </div>

      {err && <p className="error">{err}</p>}
      {loading && <p className="empty">Chargement…</p>}

      {!loading && inProgress.length > 0 && (
        <section className="live-section">
          <h2 className="live-h2">En cours</h2>
          <div className="live-grid">
            {inProgress.map((m) => <LiveCard key={m.id} m={m} />)}
          </div>
        </section>
      )}

      {!loading && upcoming.length > 0 && (
        <section className="live-section">
          <h2 className="live-h2">À venir</h2>
          <div className="live-grid">
            {upcoming.map((m) => <LiveCard key={m.id} m={m} />)}
          </div>
        </section>
      )}

      {!loading && finished.length > 0 && (
        <section className="live-section">
          <h2 className="live-h2">Terminés (récents)</h2>
          <div className="live-grid">
            {finished.map((m) => <LiveCard key={m.id} m={m} />)}
          </div>
        </section>
      )}

      {!loading && matches.length === 0 && !err && (
        <p className="empty">Aucun match disponible pour le moment.</p>
      )}
    </>
  );
}

function LiveCard({ m }: { m: LiveMatch }) {
  const setsCount = Math.max(m.sets.length, 1);
  const isLive = m.status === "inprogress";
  const finished = m.status === "finished";
  const homeWinner = m.winner_code === 1;
  const awayWinner = m.winner_code === 2;

  return (
    <article className={`live-card ${isLive ? "live-card-active" : ""}`}>
      <header className="live-card-head">
        <div className="live-tournament">
          <span className="live-tour-name">{m.tournament_name || "—"}</span>
          {m.round_name && <span className="live-round">{m.round_name}</span>}
        </div>
        <div className="live-meta">
          {m.surface && (
            <span className={surfaceChipClass(m.surface)}>
              <span className="chip-dot" />
              {surfaceLabel(m.surface)}
            </span>
          )}
          {isLive && <span className="live-badge"><span className="live-dot" aria-hidden /> LIVE</span>}
          {finished && <span className="live-badge live-badge-end">Terminé</span>}
        </div>
      </header>

      <div className="live-rows">
        <PlayerRow
          player={m.home}
          point={isLive ? m.home_point : null}
          serving={isLive && m.server_code === 1}
          winner={homeWinner}
          loser={awayWinner}
          sets={m.sets.map((s) => ({ pts: s.home, tb: s.home_tiebreak }))}
          setsCount={setsCount}
        />
        <PlayerRow
          player={m.away}
          point={isLive ? m.away_point : null}
          serving={isLive && m.server_code === 2}
          winner={awayWinner}
          loser={homeWinner}
          sets={m.sets.map((s) => ({ pts: s.away, tb: s.away_tiebreak }))}
          setsCount={setsCount}
        />
      </div>
    </article>
  );
}

function PlayerRow(props: {
  player: { name: string; country: string | null; ranking: number | null };
  point: string | null;
  serving: boolean;
  winner: boolean;
  loser: boolean;
  sets: Array<{ pts: number | null; tb: number | null }>;
  setsCount: number;
}) {
  const { player, point, serving, winner, loser, sets, setsCount } = props;
  return (
    <div className={`live-row ${winner ? "live-row-winner" : ""} ${loser ? "live-row-loser" : ""}`}>
      <div className="live-player">
        <span className="serve-dot" aria-hidden style={{ opacity: serving ? 1 : 0 }} />
        <span className="flag">{flagEmoji(player.country)}</span>
        <span className="live-name">{player.name || "?"}</span>
        {player.ranking != null && <span className="live-rank">#{player.ranking}</span>}
      </div>
      <div className="live-sets">
        {Array.from({ length: setsCount }).map((_, i) => {
          const s = sets[i];
          return (
            <span key={i} className="live-set">
              {s?.pts ?? "—"}
              {s?.tb != null && <sup className="live-tb">{s.tb}</sup>}
            </span>
          );
        })}
        {point != null && <span className="live-point">{point}</span>}
      </div>
    </div>
  );
}
