// Helpers for surface & category styling chips.

export function surfaceChipClass(surface: string | null | undefined): string {
  const s = (surface || "").toLowerCase();
  if (s.includes("hard")) return "chip surface-hard";
  if (s.includes("clay")) return "chip surface-clay";
  if (s.includes("grass")) return "chip surface-grass";
  if (s.includes("carpet")) return "chip surface-carpet";
  return "chip surface-unknown";
}

export function surfaceLabel(surface: string | null | undefined): string {
  const s = (surface || "").toLowerCase();
  if (s.includes("hard")) return "Dur";
  if (s.includes("clay")) return "Terre";
  if (s.includes("grass")) return "Gazon";
  if (s.includes("carpet")) return "Moquette";
  return surface || "—";
}

export function categoryChipClass(category: string | null | undefined): string {
  const c = (category || "").toLowerCase();
  if (c.includes("grand slam")) return "chip cat-grand-slam";
  if (c.includes("masters 1000") || c.includes("masters1000")) return "chip cat-masters-1000";
  if (c.includes("atp finals") || c === "finals") return "chip cat-atp-finals";
  if (c.includes("500")) return "chip cat-atp-500";
  if (c.includes("250")) return "chip cat-atp-250";
  return "chip";
}
