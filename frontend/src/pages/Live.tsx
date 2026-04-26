import { useEffect, useMemo, useState } from "react";
import { api, type LiveMatch } from "../api/client";
import { flagEmoji } from "../lib/flag";
import { surfaceChipClass, surfaceLabel } from "../lib/surface";

const REFRESH_MS = 60_000;

export default function Live() {
  const [matches, setMatches] = useState<LiveMatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null);

  useEffect(() => {
    let cancelled = false;
    const load = () => {
      api.live.matches()
        .then((rows) => {
          if (cancelled) return;
          setMatches(rows);
          setUpdatedAt(new Date());
          setErr(null);
        })
        .catch((e) => !cancelled && setErr(String(e)))
        .finally(() => !cancelled && setLoading(false));
    };
    load();
    const id = setInterval(load, REFRESH_MS);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

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
      <div className="page-head">
        <h1>
          <span className="live-dot" aria-hidden /> En direct
        </h1>
        <p className="sub">
          {inProgress.length} match{inProgress.length > 1 ? "s" : ""} en cours
          {updatedAt && ` — actualisé à ${updatedAt.toLocaleTimeString("fr-FR")}`}
        </p>
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
