import { createContext, ReactNode, useCallback, useContext, useEffect, useState } from "react";
import { api, get, send, tokens } from "../services/api";
import type { User } from "../types";

interface AuthValue { user: User | null; loading: boolean;
  login(email: string, password: string): Promise<User>;
  register(data: { email: string; password: string; full_name: string; phone?: string }): Promise<User>;
  logout(): Promise<void>; reload(): Promise<void>; setSession(d: any): void; }

const Ctx = createContext<AuthValue>(null!);
export const useAuth = () => useContext(Ctx);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  const reload = useCallback(async () => {
    if (!tokens.access) { setUser(null); return; }
    try { setUser((await get<{ user: User }>("/auth/me")).user); } catch { tokens.clear(); setUser(null); }
  }, []);

  useEffect(() => { reload().finally(() => setLoading(false)); }, [reload]);
  useEffect(() => {
    const h = () => { tokens.clear(); setUser(null); };
    window.addEventListener("sss:logout", h); return () => window.removeEventListener("sss:logout", h);
  }, []);

  const setSession = (d: any) => { tokens.set(d.access_token, d.refresh_token); setUser(d.user); };
  const login = async (email: string, password: string) => { const d = await send<any>("post", "/auth/login", { email, password }); setSession(d); return d.user; };
  const register = async (data: any) => { const d = await send<any>("post", "/auth/register", data); setSession(d); return d.user; };
  const logout = async () => {
    try { await api.post("/auth/logout", { refresh_token: tokens.refresh }); } catch { /* token may already be invalid */ }
    tokens.clear(); setUser(null);
  };
  return <Ctx.Provider value={{ user, loading, login, register, logout, reload, setSession }}>{children}</Ctx.Provider>;
}
