import { useState } from "react";
import { Link, NavLink } from "react-router-dom";

export default function Header() {
  const [openRanking, setOpenRanking] = useState(false);

  return (
    <header className="topbar">
      <Link to="/" className="brand">🎾 Tennis Stats</Link>
      <nav className="nav">
        <div
          className="dropdown"
          onMouseEnter={() => setOpenRanking(true)}
          onMouseLeave={() => setOpenRanking(false)}
        >
          <button className="dropdown-trigger">Classements ▾</button>
          {openRanking && (
            <div className="dropdown-menu">
              <NavLink to="/rankings/atp">ATP Live</NavLink>
              <NavLink to="/rankings/race">ATP Race Live</NavLink>
              <NavLink to="/rankings/elo">Elo</NavLink>
            </div>
          )}
        </div>
        <NavLink to="/calendar">Calendrier ATP</NavLink>
        <NavLink to="/players">Fiche Joueur</NavLink>
      </nav>
    </header>
  );
}
