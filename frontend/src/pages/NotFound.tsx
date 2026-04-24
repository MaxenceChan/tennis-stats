import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div>
      <h1>404</h1>
      <p>Page introuvable. <Link to="/">Retour à l'accueil</Link></p>
    </div>
  );
}
