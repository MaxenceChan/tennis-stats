import { useState } from "react";
import { Link, NavLink } from "react-router-dom";

export default function Header() {
  const [openRanking, setOpenRanking] = useState(false);

  return (
    <header className="topbar">
      <Link to="/" className="brand" aria-label="Tennis Stats accueil">
        <span className="brand-ball" aria-hidden />
        <span className="brand-text">Tennis Stats</span>
      </Link>
      <nav className="nav">
        <div
          className="dropdown"
          onMouseEnter={() => setOpenRanking(true)}
          onMouseLeave={() => setOpenRanking(false)}
        >
          <button className="dropdown-trigger" aria-haspopup="menu" aria-expanded={openRanking}>
            Classements
            <svg width="10" height="10" viewBox="0 0 10 10" aria-hidden>
              <path d="M2 3.5l3 3 3-3" stroke="currentColor" strokeWidth="1.4" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
          {openRanking && (
            <div className="dropdown-menu" role="menu">
              <NavLink to="/rankings/atp">ATP Live</NavLink>
              <NavLink to="/rankings/race">ATP Race</NavLink>
              <NavLink to="/rankings/elo">Elo</NavLink>
            </div>
          )}
        </div>
        <NavLink to="/calendar">Calendrier</NavLink>
        <NavLink to="/players">Fiche joueur</NavLink>
      </nav>
    </header>
  );
}
