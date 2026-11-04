import { createContext, ReactNode, useCallback, useContext, useState } from "react";

type Toast = { id: number; text: string; kind: "success" | "error" };
const Ctx = createContext<{ notify(text: string, kind?: Toast["kind"]): void }>({ notify() {} });
export const useToast = () => useContext(Ctx);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<Toast[]>([]);
  const notify = useCallback((text: string, kind: Toast["kind"] = "success") => {
    const id = Date.now() + Math.random();
    setItems((x) => [...x, { id, text, kind }]);
    setTimeout(() => setItems((x) => x.filter((t) => t.id !== id)), 4500);
  }, []);
  return (
    <Ctx.Provider value={{ notify }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 space-y-2">
        {items.map((t) => (
          <div key={t.id} role="status" className={`max-w-sm rounded-lg px-4 py-3 text-sm text-white shadow-lg ${t.kind === "error" ? "bg-red-600" : "bg-navy-800"}`}>{t.text}</div>
        ))}
      </div>
    </Ctx.Provider>
  );
}
