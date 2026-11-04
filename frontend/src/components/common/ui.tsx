import { AlertTriangle, Inbox, Loader2 } from "lucide-react";
import { ReactNode } from "react";
import { label } from "../../utils/format";

export const Spinner = () => (
  <div className="flex justify-center py-12" aria-label="Loading"><Loader2 className="h-6 w-6 animate-spin text-royal-500" /></div>
);

export const ErrorState = ({ message, onRetry }: { message: string; onRetry?: () => void }) => (
  <div className="card flex flex-col items-center gap-3 text-center">
    <AlertTriangle className="h-6 w-6 text-red-500" /><p className="text-sm">{message}</p>
    {onRetry && <button className="btn-secondary" onClick={onRetry}>Try again</button>}
  </div>
);

export const Empty = ({ title, text, action }: { title: string; text?: string; action?: ReactNode }) => (
  <div className="card flex flex-col items-center gap-2 py-10 text-center">
    <Inbox className="h-8 w-8 text-slate-400" /><h3 className="font-semibold">{title}</h3>
    {text && <p className="max-w-md text-sm text-slate-500">{text}</p>}{action}
  </div>
);

export const PageHeader = ({ title, subtitle, actions }: { title: string; subtitle?: string; actions?: ReactNode }) => (
  <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
    <div><h1 className="text-2xl font-semibold text-navy-800 dark:text-white">{title}</h1>
      {subtitle && <p className="text-sm text-slate-500">{subtitle}</p>}</div>
    <div className="flex flex-wrap gap-2">{actions}</div>
  </div>
);

const TONES: Record<string, string> = {
  verified: "bg-emerald-100 text-emerald-800", expired: "bg-slate-200 text-slate-700",
  unverified: "bg-amber-100 text-amber-800", needs_review: "bg-orange-100 text-orange-800",
  sent: "bg-emerald-100 text-emerald-800", failed: "bg-red-100 text-red-800", skipped: "bg-slate-200 text-slate-700",
  pending: "bg-blue-100 text-blue-800", approved: "bg-emerald-100 text-emerald-800", rejected: "bg-red-100 text-red-800",
  applied: "bg-indigo-100 text-indigo-800", open: "bg-amber-100 text-amber-800", resolved: "bg-emerald-100 text-emerald-800",
};
export const Badge = ({ value, text }: { value: string; text?: string }) => (
  <span className={`inline-block rounded-full px-2 py-0.5 text-xs font-medium ${TONES[value] || "bg-violet-100 text-violet-800"}`}>{text || label(value)}</span>
);

export const Stat = ({ icon, title, value }: { icon: ReactNode; title: string; value: ReactNode }) => (
  <div className="card flex items-center gap-4">
    <div className="rounded-lg bg-royal-500/10 p-3 text-royal-600">{icon}</div>
    <div><p className="text-xs text-slate-500">{title}</p><p className="text-xl font-semibold">{value}</p></div>
  </div>
);

export function Field({ label: l, children }: { label: string; children: ReactNode }) {
  return <label className="block"><span className="label">{l}</span>{children}</label>;
}

export function Select({ value, onChange, options, placeholder }: {
  value: string | number | null | undefined; onChange(v: string): void;
  options: (string | { value: string | number; label: string })[]; placeholder?: string; }) {
  return (
    <select className="input" value={value ?? ""} onChange={(e) => onChange(e.target.value)}>
      {placeholder !== undefined && <option value="">{placeholder}</option>}
      {options.map((o) => typeof o === "string"
        ? <option key={o} value={o}>{label(o)}</option>
        : <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  );
}

export function Pager({ page, pages, onPage }: { page: number; pages: number; onPage(p: number): void }) {
  if (pages <= 1) return null;
  return (
    <div className="mt-4 flex items-center justify-center gap-3 text-sm">
      <button className="btn-secondary" disabled={page <= 1} onClick={() => onPage(page - 1)}>Previous</button>
      <span>Page {page} of {pages}</span>
      <button className="btn-secondary" disabled={page >= pages} onClick={() => onPage(page + 1)}>Next</button>
    </div>
  );
}

export function Modal({ title, onClose, children }: { title: string; onClose(): void; children: ReactNode }) {
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <div className="card max-h-[90vh] w-full max-w-2xl overflow-y-auto" onClick={(e) => e.stopPropagation()} role="dialog">
        <div className="mb-4 flex items-center justify-between"><h2 className="text-lg font-semibold">{title}</h2>
          <button className="text-slate-400" onClick={onClose} aria-label="Close">✕</button></div>
        {children}
      </div>
    </div>
  );
}
