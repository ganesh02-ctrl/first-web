import { useState } from "react";
import { Link } from "react-router-dom";
import { Badge, Empty, ErrorState, PageHeader, Spinner } from "../components/common/ui";
import { useToast } from "../contexts/ToastContext";
import { useApi } from "../hooks/useApi";
import { errorMessage, get, send } from "../services/api";
import type { Tracked as T } from "../types";
import { date } from "../utils/format";

export default function Tracked() {
  const [bookmarked, setBookmarked] = useState(false); const { notify } = useToast();
  const { data, loading, error, reload } = useApi(() => get<T[]>("/tracking", bookmarked ? { bookmarked: "true" } : {}), [bookmarked]);
  const untrack = async (id: number) => { try { await send("delete", `/tracking/${id}`); notify("Removed"); reload(); } catch (e) { notify(errorMessage(e), "error"); } };
  return (
    <>
      <PageHeader title="Tracked scholarships" actions={<label className="flex items-center gap-2 text-sm">
        <input type="checkbox" checked={bookmarked} onChange={(e) => setBookmarked(e.target.checked)} />Bookmarked only</label>} />
      {loading ? <Spinner /> : error ? <ErrorState message={error} onRetry={reload} /> : data!.length === 0 ?
        <Empty title="Nothing tracked yet" text="Track a scholarship to get deadline reminders." action={<Link className="btn-primary" to="/scholarships">Browse</Link>} /> :
        <div className="card overflow-x-auto"><table className="table w-full"><thead><tr><th>Scholarship</th><th>Closes</th><th>Status</th><th>Application</th><th>Reminders</th><th /></tr></thead>
          <tbody>{data!.map((t) => <tr key={t.id}>
            <td><Link className="text-royal-600" to={`/scholarships/${t.scholarship.id}`}>{t.is_bookmarked ? "★ " : ""}{t.scholarship.title}</Link></td>
            <td>{date(t.scholarship.application_close_date)}</td><td><Badge value={t.scholarship.effective_status} /></td>
            <td>{t.application?.status_label || "—"}</td><td>{t.reminders_enabled ? "On" : "Off"}</td>
            <td><button className="text-sm text-red-600" onClick={() => untrack(t.scholarship.id)}>Remove</button></td></tr>)}</tbody></table></div>}
    </>
  );
}
