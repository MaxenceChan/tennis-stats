// ISO 3166-1 alpha-3 → emoji flag (most tennis-active nations).
// Falls back to empty string if unknown.

const ISO3_TO_ISO2: Record<string, string> = {
  ARG: "AR", AUS: "AU", AUT: "AT", BEL: "BE", BIH: "BA", BLR: "BY", BOL: "BO",
  BRA: "BR", BUL: "BG", CAN: "CA", CHI: "CL", CHN: "CN", COL: "CO", CRO: "HR",
  CYP: "CY", CZE: "CZ", DEN: "DK", DOM: "DO", ECU: "EC", EGY: "EG", ESP: "ES",
  EST: "EE", FIN: "FI", FRA: "FR", GBR: "GB", GEO: "GE", GER: "DE", GRE: "GR",
  HUN: "HU", IND: "IN", INA: "ID", IRL: "IE", ISR: "IL", ITA: "IT", JPN: "JP",
  KAZ: "KZ", KOR: "KR", LAT: "LV", LIB: "LB", LTU: "LT", LUX: "LU", MAR: "MA",
  MDA: "MD", MEX: "MX", MON: "MC", NED: "NL", NOR: "NO", NZL: "NZ", PAR: "PY",
  PER: "PE", PHI: "PH", POL: "PL", POR: "PT", PUR: "PR", QAT: "QA", ROU: "RO",
  RSA: "ZA", RUS: "RU", SLO: "SI", SRB: "RS", SUI: "CH", SVK: "SK", SWE: "SE",
  THA: "TH", TPE: "TW", TUN: "TN", TUR: "TR", UKR: "UA", URU: "UY", USA: "US",
  UZB: "UZ", VEN: "VE", VIE: "VN", ZIM: "ZW",
};

export function flagEmoji(iso3: string | null | undefined): string {
  if (!iso3) return "";
  const iso2 = ISO3_TO_ISO2[iso3.toUpperCase()];
  if (!iso2) return "";
  // Regional indicator symbols
  const A = 0x1f1e6;
  return String.fromCodePoint(
    A + (iso2.charCodeAt(0) - 65),
    A + (iso2.charCodeAt(1) - 65),
  );
}
