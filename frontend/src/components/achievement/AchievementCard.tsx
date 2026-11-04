import { MapPin } from "lucide-react";
import type { Achievement } from "../../types";
import { date, label, mapUrl } from "../../utils/format";

export default function AchievementCard({ a, actions }: { a: Achievement; actions?: React.ReactNode }) {
  const map = a.latitude != null && a.longitude != null ? mapUrl(a.latitude, a.longitude) : null;
  return (
    <div className="card">
      <div className="flex items-start justify-between"><h3 className="font-semibold">{a.title}</h3>
        <span className="rounded-full bg-violet-100 px-2 text-xs text-violet-800">{label(a.category)}</span></div>
      <p className="text-sm text-slate-500">{a.organization} · {date(a.achieved_on)}{a.rank_position ? ` · ${a.rank_position}` : ""}</p>
      {a.description && <p className="mt-2 text-sm">{a.description}</p>}
      {a.location_name && <p className="mt-2 flex items-center gap-1 text-xs text-slate-500"><MapPin className="h-3 w-3" />
        {map ? <a className="text-royal-600" href={map} target="_blank" rel="noopener noreferrer">{a.location_name}</a> : a.location_name}</p>}
      {actions && <div className="mt-3 flex gap-3 text-sm">{actions}</div>}
    </div>
  );
}
