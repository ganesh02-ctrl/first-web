import { CalendarClock, Landmark } from "lucide-react";
import { Link } from "react-router-dom";
import type { ScholarshipSummary } from "../../types";
import { date, label } from "../../utils/format";
import { Badge } from "../common/ui";

export default function ScholarshipCard({ s }: { s: ScholarshipSummary }) {
  return (
    <Link to={`/scholarships/${s.id}`} className="card block transition hover:-translate-y-0.5 hover:border-royal-500">
      <div className="mb-2 flex items-start justify-between gap-2">
        <h3 className="font-semibold text-navy-800 dark:text-white">{s.title}</h3><Badge value={s.effective_status} />
      </div>
      <p className="flex items-center gap-1 text-sm text-slate-500"><Landmark className="h-4 w-4" />{s.provider_name}</p>
      <p className="mt-1 text-sm">{s.amount_text || "Amount: see official source"}</p>
      <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-slate-500">
        <span className="flex items-center gap-1"><CalendarClock className="h-4 w-4" />
          {s.application_close_date ? `Closes ${date(s.application_close_date)}${s.days_left != null && s.days_left >= 0 ? ` (${s.days_left}d left)` : ""}` : "No closing date listed"}</span>
        <span>· {label(s.scholarship_type)}</span><span>· {s.state || "All India"}</span>
      </div>
      <p className="mt-2 text-xs text-slate-400">Source: {s.official_source_name} · verified {date(s.last_verified_at)}</p>
    </Link>
  );
}
