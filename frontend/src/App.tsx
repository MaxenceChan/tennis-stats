import { Route, Routes } from "react-router-dom";
import Header from "./components/Header";
import Home from "./pages/Home";
import RankingsAtp from "./pages/RankingsAtp";
import RankingsRace from "./pages/RankingsRace";
import RankingsElo from "./pages/RankingsElo";
import Calendar from "./pages/Calendar";
import PlayerSearch from "./pages/PlayerSearch";
import PlayerDetail from "./pages/PlayerDetail";
import NotFound from "./pages/NotFound";

export default function App() {
  return (
    <>
      <Header />
      <main className="container">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/rankings/atp" element={<RankingsAtp />} />
          <Route path="/rankings/race" element={<RankingsRace />} />
          <Route path="/rankings/elo" element={<RankingsElo />} />
          <Route path="/calendar" element={<Calendar />} />
          <Route path="/players" element={<PlayerSearch />} />
          <Route path="/players/:playerId" element={<PlayerDetail />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
    </>
  );
}
