import axios, { AxiosError } from "axios";

let rawBase = (import.meta.env.VITE_API_BASE_URL || "").trim();
if (rawBase && !rawBase.startsWith("http://") && !rawBase.startsWith("https://") && !rawBase.startsWith("/")) {
  rawBase = `https://${rawBase}`;
}
if (rawBase && !rawBase.endsWith("/api") && !rawBase.endsWith("/api/")) {
  rawBase = `${rawBase.replace(/\/+$/, "")}/api`;
}
export const API_BASE = rawBase || (import.meta.env.PROD ? "/api" : "http://localhost:5000/api");
const ACCESS = "sss_access", REFRESH = "sss_refresh";

export const tokens = {
  get access() { return localStorage.getItem(ACCESS); },
  get refresh() { return localStorage.getItem(REFRESH); },
  set(access: string, refresh?: string) { localStorage.setItem(ACCESS, access); if (refresh) localStorage.setItem(REFRESH, refresh); },
  clear() { localStorage.removeItem(ACCESS); localStorage.removeItem(REFRESH); },
};

export const api = axios.create({ baseURL: API_BASE });

api.interceptors.request.use((config) => {
  if (tokens.access && !config.headers.Authorization) config.headers.Authorization = `Bearer ${tokens.access}`;
  return config;
});

let refreshing: Promise<string | null> | null = null;
async function refreshAccess(): Promise<string | null> {
  if (!tokens.refresh) return null;
  try {
    const r = await axios.post(`${API_BASE}/auth/refresh`, null, { headers: { Authorization: `Bearer ${tokens.refresh}` } });
    tokens.set(r.data.data.access_token);
    return r.data.data.access_token;
  } catch { tokens.clear(); return null; }
}

api.interceptors.response.use((r) => r, async (error: AxiosError) => {
  const original = error.config as any;
  const url = original?.url || "";
  if (error.response?.status === 401 && original && !original._retry && !url.includes("/auth/")) {
    original._retry = true;
    refreshing = refreshing || refreshAccess().finally(() => { refreshing = null; });
    const fresh = await refreshing;
    if (fresh) { original.headers.Authorization = `Bearer ${fresh}`; return api(original); }
    window.dispatchEvent(new Event("sss:logout"));
  }
  return Promise.reject(error);
});

export function errorMessage(err: unknown): string {
  const e = err as AxiosError<any>;
  const body = e?.response?.data?.error;
  if (body) {
    const d = body.details;
    if (d && typeof d === "object" && !Array.isArray(d)) {
      const first = Object.entries(d)[0];
      if (first) return `${body.message}: ${first[0]} — ${JSON.stringify(first[1])}`;
    }
    if (Array.isArray(d)) return `${body.message}: ${d.join(" ")}`;
    return body.message;
  }
  return e?.message || "Something went wrong";
}

export async function get<T>(url: string, params?: object): Promise<T> { return (await api.get(url, { params })).data.data; }
export async function getPage<T>(url: string, params?: object) {
  const r = await api.get(url, { params }); return { items: r.data.data as T[], meta: r.data.meta };
}
export async function send<T>(method: "post" | "put" | "patch" | "delete", url: string, body?: unknown): Promise<T> {
  return (await api.request({ method, url, data: body })).data.data;
}

/** Fetch a protected file with the JWT and open/save it (no public file URLs). */
export async function openFile(url: string, filename?: string) {
  const r = await api.get(url, { responseType: "blob" });
  const href = URL.createObjectURL(r.data);
  if (filename) { const a = document.createElement("a"); a.href = href; a.download = filename; a.click(); }
  else window.open(href, "_blank", "noopener");
  setTimeout(() => URL.revokeObjectURL(href), 60000);
}
