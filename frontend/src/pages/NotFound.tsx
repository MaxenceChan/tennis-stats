import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <section className="hero" style={{ textAlign: "center" }}>
      <span className="hero-eyebrow">Erreur 404</span>
      <h1>Out !</h1>
      <p className="lead" style={{ margin: "0 auto" }}>
        La balle est sortie du court — cette page n'existe pas.
      </p>
      <p style={{ marginTop: "1.5rem" }}>
        <Link to="/" className="player-link" style={{ color: "var(--ball)" }}>
          ← Retour à l'accueil
        </Link>
      </p>
    </section>
  );
}
