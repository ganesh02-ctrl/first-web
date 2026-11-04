import { createContext, ReactNode, useContext, useEffect, useState } from "react";

const Ctx = createContext<{ dark: boolean; toggle(): void }>({ dark: false, toggle() {} });
export const useTheme = () => useContext(Ctx);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [dark, setDark] = useState(() => localStorage.getItem("sss_theme") === "dark");
  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
    localStorage.setItem("sss_theme", dark ? "dark" : "light");
  }, [dark]);
  return <Ctx.Provider value={{ dark, toggle: () => setDark((d) => !d) }}>{children}</Ctx.Provider>;
}
