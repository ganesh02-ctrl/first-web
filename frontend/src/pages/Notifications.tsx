import { useState } from "react";
import { Link } from "react-router-dom";
import { Badge, Empty, ErrorState, PageHeader, Pager, Spinner } from "../components/common/ui";
import { useToast } from "../contexts/ToastContext";
import { useApi } from "../hooks/useApi";
import { errorMessage, getPage, send } from "../services/api";
import type { Notification } from "../types";
import { date, label } from "../utils/format";

export default function Notifications() {
  const { notify } = useToast(); const [page, setPage] = useState(1); const [unread, setUnread] = useState(false);
  const { data, loading, error, reload } = useApi(() => getPage<Notification>("/notifications", { page, unread: unread || undefined }), [page, unread]);
  const run = async (fn: () => Promise<unknown>) => { try { await fn(); reload(); } catch (e) { notify(errorMessage(e), "error"); } };
  return (
    <>
      <PageHeader title="Notification center" actions={<>
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={unread} onChange={(e) => { setPage(1); setUnread(e.target.checked); }} />Unread only</label>
        <button className="btn-secondary" onClick={() => run(() => send("post", "/notifications/read-all"))}>Mark all read</button></>} />
      {loading ? <Spinner /> : error ? <ErrorState message={error} onRetry={reload} /> : data!.items.length === 0 ? <Empty title="No notifications" /> : <>
        <div className="space-y-3">{data!.items.map((n) => (
          <div key={n.id} className={`card ${n.is_read ? "opacity-75" : "border-royal-500"}`}>
            <div className="flex justify-between gap-2"><h3 className="font-semibold">{n.title}</h3><span className="text-xs text-slate-500">{date(n.created_at)}</span></div>
            <p className="text-sm">{n.message}</p>
            <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
              {n.deliveries.map((d) => <span key={d.channel} title={d.last_error || ""}>{label(d.channel)}: <Badge value={d.status} /></span>)}
              {n.link && <Link className="text-royal-600" to={n.link}>Open</Link>}
              {!n.is_read && <button className="text-royal-600" onClick={() => run(() => send("post", `/notifications/${n.id}/read`))}>Mark read</button>}
              <button className="text-red-600" onClick={() => run(() => send("delete", `/notifications/${n.id}`))}>Delete</button>
            </div>
          </div>))}</div>
        <Pager page={data!.meta.page} pages={data!.meta.pages} onPage={setPage} /></>}
    </>
  );
}
