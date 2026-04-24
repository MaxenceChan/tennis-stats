import { Link } from "react-router-dom";

export default function Home() {
  return (
    <section className="hero">
      <h1>Tennis Stats</h1>
      <p className="lead">
        Classements ATP en direct, calendrier de la tournée et fiches détaillées
        des joueurs — données agrégées depuis Tennis Abstract, live-tennis.eu et Wikipedia.
      </p>
      <div className="cards">
        <Link to="/rankings/atp" className="card">
          <h3>ATP Live</h3>
          <p>Classement officiel mis à jour quotidiennement.</p>
        </Link>
        <Link to="/rankings/race" className="card">
          <h3>ATP Race Live</h3>
          <p>Course aux ATP Finals depuis le début de saison.</p>
        </Link>
        <Link to="/rankings/elo" className="card">
          <h3>Classement Elo</h3>
          <p>Calculé sur tous les matches connus, par surface.</p>
        </Link>
        <Link to="/calendar" className="card">
          <h3>Calendrier</h3>
          <p>Tournois ATP : 250, 500, Masters 1000, Grand Chelem.</p>
        </Link>
        <Link to="/players" className="card">
          <h3>Fiche Joueur</h3>
          <p>Recherche par nom — résultats récents, titres, head-to-head.</p>
        </Link>
      </div>
    </section>
  );
}
