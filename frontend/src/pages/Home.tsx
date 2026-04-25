import { Link } from "react-router-dom";

const TILES = [
  {
    to: "/rankings/atp",
    icon: "🏆",
    title: "ATP Live",
    desc: "Classement officiel mis à jour quotidiennement.",
  },
  {
    to: "/rankings/race",
    icon: "🏁",
    title: "Race to Turin",
    desc: "Course aux ATP Finals depuis le début de saison.",
  },
  {
    to: "/rankings/elo",
    icon: "📊",
    title: "Classement Elo",
    desc: "Calculé sur tous les matches connus, par surface.",
  },
  {
    to: "/calendar",
    icon: "🗓️",
    title: "Calendrier",
    desc: "ATP 250, 500, Masters 1000, Grand Chelem.",
  },
  {
    to: "/players",
    icon: "🎾",
    title: "Fiche joueur",
    desc: "Recherche par nom — résultats, titres, head-to-head.",
  },
];

export default function Home() {
  return (
    <section>
      <div className="hero">
        <span className="hero-eyebrow">
          <span className="chip-dot" /> Saison ATP en cours
        </span>
        <h1>Le tennis pro,<br />en chiffres et en détails.</h1>
        <p className="lead">
          Classements ATP en direct, calendrier de la tournée, fiches détaillées,
          historique des matchs et statistiques par surface — agrégés depuis
          Jeff Sackmann, BallDontLie et Wikipedia.
        </p>
      </div>

      <div className="cards">
        {TILES.map((t) => (
          <Link key={t.to} to={t.to} className="card">
            <span className="card-icon">{t.icon}</span>
            <h3>{t.title}</h3>
            <p>{t.desc}</p>
          </Link>
        ))}
      </div>
    </section>
  );
}
