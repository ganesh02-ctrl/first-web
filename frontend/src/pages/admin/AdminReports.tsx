import { useState } from "react";
import { Badge, Empty, ErrorState, PageHeader, Pager, Select, Spinner } from "../../components/common/ui";
import { useToast } from "../../contexts/ToastContext";
import { useApi } from "../../hooks/useApi";
import { errorMessage, get, getPage, send } from "../../services/api";
import type { Category } from "../../types";
import { date, label } from "../../utils/format";

const TABS = ["reports", "categories", "deliveries", "audit"] as const;

export default function AdminReports() {
  const [tab, setTab] = useState<(typeof TABS)[number]>("reports");
  return (
    <>
      <PageHeader title="Reports, categories & logs" />
      <div className="mb-4 flex gap-2">{TABS.map((t) => <button key={t} className={tab === t ? "btn-primary" : "btn-secondary"} onClick={() => setTab(t)}>{label(t)}</button>)}</div>
      {tab === "reports" && <Reports />}{tab === "categories" && <Categories />}{tab === "deliveries" && <Deliveries />}{tab === "audit" && <Audit />}
    </>
  );
}

function Reports() {
  const { notify } = useToast(); const [status, setStatus] = useState("open"); const [page, setPage] = useState(1);
  const { data, loading, error, reload } = useApi(() => getPage<any>("/admin/reports", { status: status || undefined, page }), [status, page]);
  const update = async (id: number, s: string) => { const notes = prompt("Admin notes (optional)") ?? undefined;
    try { await send("patch", `/admin/reports/${id}`, { status: s, admin_notes: notes || null }); reload(); } catch (e) { notify(errorMessage(e), "error"); } };
  return <>
    <div className="mb-3 w-48"><Select value={status} onChange={setStatus} options={["open", "reviewing", "resolved", "dismissed"]} placeholder="All" /></div>
    {loading ? <Spinner /> : error ? <ErrorState message={error} /> : data!.items.length === 0 ? <Empty title="No reports" /> : <>
      <div className="space-y-3">{data!.items.map((r) => <div key={r.id} className="card text-sm">
        <div className="flex justify-between"><b>{r.scholarship_title}</b><Badge value={r.status} /></div>
        <p>{label(r.reason)} — {r.details}</p><p className="text-xs text-slate-500">{r.reporter_email} · {date(r.created_at)}{r.admin_notes ? ` · Notes: ${r.admin_notes}` : ""}</p>
        <div className="mt-2 flex gap-3"><a className="text-royal-600" href={`/admin/scholarships/${r.scholarship_id}`}>Open record</a>
          {["reviewing", "resolved", "dismissed"].map((s) => <button key={s} className="text-royal-600" onClick={() => update(r.id, s)}>{label(s)}</button>)}</div></div>)}</div>
      <Pager page={data!.meta.page} pages={data!.meta.pages} onPage={setPage} /></>}
  </>;
}

function Categories() {
  const { notify } = useToast();
  const { data, loading, reload } = useApi(() => get<Category[]>("/admin/categories"));
  const run = async (fn: () => Promise<unknown>) => { try { await fn(); reload(); } catch (e) { notify(errorMessage(e), "error"); } };
  if (loading) return <Spinner />;
  return <div className="card space-y-2 text-sm">
    <button className="btn-primary" onClick={() => { const n = prompt("Category name"); if (n) run(() => send("post", "/admin/categories", { name: n })); }}>Add category</button>
    {data!.length === 0 && <p className="text-slate-500">No categories yet.</p>}
    {data!.map((c) => <div key={c.id} className="flex justify-between border-t pt-2"><span>{c.name} ({c.scholarship_count})</span>
      <span className="space-x-3"><button className="text-royal-600" onClick={() => { const n = prompt("Rename", c.name); if (n) run(() => send("put", `/admin/categories/${c.id}`, { name: n, description: c.description })); }}>Rename</button>
        <button className="text-red-600" onClick={() => confirm("Delete category? Scholarships keep existing without it.") && run(() => send("delete", `/admin/categories/${c.id}`))}>Delete</button></span></div>)}
  </div>;
}

function Deliveries() {
  const [status, setStatus] = useState(""); const [channel, setChannel] = useState(""); const [page, setPage] = useState(1);
  const { data, loading, error } = useApi(() => getPage<any>("/admin/notifications/deliveries", { status: status || undefined, channel: channel || undefined, page }), [status, channel, page]);
  return <>
    <div className="mb-3 flex gap-2"><div className="w-40"><Select value={channel} onChange={setChannel} options={["in_app", "email", "sms"]} placeholder="All channels" /></div>
      <div className="w-40"><Select value={status} onChange={setStatus} options={["pending", "sent", "failed", "skipped"]} placeholder="All statuses" /></div></div>
    {loading ? <Spinner /> : error ? <ErrorState message={error} /> : data!.items.length === 0 ? <Empty title="No deliveries" /> : <>
      <div className="card overflow-x-auto"><table className="table w-full"><thead><tr><th>When</th><th>User</th><th>Notification</th><th>Channel</th><th>Status</th><th>Attempts</th><th>Error</th></tr></thead>
        <tbody>{data!.items.map((d) => <tr key={d.id}><td>{date(d.created_at)}</td><td>{d.user_email}</td><td>{d.notification_title}</td><td>{label(d.channel)}</td>
          <td><Badge value={d.status} /></td><td>{d.attempts}</td><td className="max-w-xs truncate" title={d.last_error || ""}>{d.last_error || "—"}</td></tr>)}</tbody></table></div>
      <Pager page={data!.meta.page} pages={data!.meta.pages} onPage={setPage} /></>}
  </>;
}

function Audit() {
  const [page, setPage] = useState(1);
  const { data, loading, error } = useApi(() => getPage<any>("/admin/logs", { page }), [page]);
  if (loading) return <Spinner />;
  if (error) return <ErrorState message={error} />;
  return <>
    <div className="card overflow-x-auto"><table className="table w-full"><thead><tr><th>When</th><th>Admin</th><th>Action</th><th>Entity</th><th>Details</th></tr></thead>
      <tbody>{data!.items.map((l) => <tr key={l.id}><td>{date(l.created_at)}</td><td>{l.admin_email}</td><td>{l.action}</td><td>{l.entity_type} #{l.entity_id ?? "—"}</td>
        <td className="max-w-sm truncate text-xs">{JSON.stringify(l.details)}</td></tr>)}</tbody></table></div>
    <Pager page={data!.meta.page} pages={data!.meta.pages} onPage={setPage} /></>;
}
