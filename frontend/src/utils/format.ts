export const label = (s?: string | null) => (s ? s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()) : "—");
export const date = (s?: string | null) =>
  s ? new Date(s.length === 10 ? s + "T00:00:00" : s).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" }) : "—";
export const inr = (n?: number | null) => (n == null ? "—" : "₹" + n.toLocaleString("en-IN"));
export const bytes = (n: number) => (n < 1024 * 1024 ? `${(n / 1024).toFixed(0)} KB` : `${(n / 1048576).toFixed(1)} MB`);
export const mapUrl = (lat: number, lon: number) =>
  import.meta.env.VITE_MAPS_PROVIDER === "none" ? null : `https://www.openstreetmap.org/?mlat=${lat}&mlon=${lon}#map=14/${lat}/${lon}`;
export const clean = <T extends object>(o: T) =>
  Object.fromEntries(Object.entries(o).map(([k, v]) => [k, v === "" ? null : v])) as T;
