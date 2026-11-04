import { useState } from "react";
import { Empty, ErrorState, Modal, PageHeader, Pager, Select, Spinner } from "../../components/common/ui";
import { useToast } from "../../contexts/ToastContext";
import { useApi } from "../../hooks/useApi";
import { errorMessage, get, getPage, send } from "../../services/api";
import type { User } from "../../types";
import { date, label } from "../../utils/format";

export default function AdminStudents() {
  const { notify } = useToast();
  const [q, setQ] = useState(""); const [role, setRole] = useState(""); const [page, setPage] = useState(1);
  const { data, loading, error, reload } = useApi(() => getPage<User>("/admin/users", { q: q || undefined, role: role || undefined, page }), [q, role, page]);
  const [detail, setDetail] = useState<any>(null);
  const run = async (fn: () => Promise<unknown>, ok: string) => { try { await fn(); notify(ok); reload(); } catch (e) { notify(errorMessage(e), "error"); } };
  return (
    <>
      <PageHeader title="Student management" />
      <div className="mb-4 flex gap-2"><input className="input" placeholder="Search email, name or college" value={q} onChange={(e) => { setPage(1); setQ(e.target.value); }} />
        <div className="w-40"><Select value={role} onChange={(v) => { setPage(1); setRole(v); }} options={["student", "admin"]} placeholder="All roles" /></div></div>
      {loading ? <Spinner /> : error ? <ErrorState message={error} onRetry={reload} /> : data!.items.length === 0 ? <Empty title="No users found" /> : <>
        <div className="card overflow-x-auto"><table className="table w-full"><thead><tr><th>Name</th><th>Email</th><th>Role</th><th>Status</th><th>Joined</th><th /></tr></thead>
          <tbody>{data!.items.map((u) => <tr key={u.id}><td>{u.full_name}</td><td>{u.email}</td><td>{label(u.role)}</td><td>{u.is_active ? "Active" : "Disabled"}</td><td>{date(u.created_at)}</td>
            <td className="space-x-3 text-sm"><button className="text-royal-600" onClick={async () => setDetail(await get(`/admin/users/${u.id}`))}>View</button>
              <button className="text-royal-600" onClick={() => run(() => send("patch", `/admin/users/${u.id}`, { is_active: !u.is_active }), "Updated")}>{u.is_active ? "Disable" : "Enable"}</button>
              <button className="text-red-600" onClick={() => confirm(`Permanently delete ${u.email} and all their data?`) && run(() => send("delete", `/admin/users/${u.id}`), "Deleted")}>Delete</button></td></tr>)}</tbody></table></div>
        <Pager page={data!.meta.page} pages={data!.meta.pages} onPage={setPage} /></>}
      {detail && <Modal title={detail.email} onClose={() => setDetail(null)}>
        <p className="text-sm">Role: {detail.role} · Verified: {detail.email_verified ? "yes" : "no"} · Last login: {date(detail.last_login_at)}</p>
        <p className="mt-2 text-sm">Tracked {detail.stats.tracked} · Applications {detail.stats.applications} · Achievements {detail.stats.achievements} · Documents {detail.stats.documents} · Semesters {detail.stats.semesters}</p>
        <p className="mt-2 text-sm">{detail.profile?.college} {detail.profile?.degree} {detail.profile?.state}</p>
        <button className="btn-secondary mt-4" onClick={() => run(() => send("patch", `/admin/users/${detail.id}`, { role: detail.role === "admin" ? "student" : "admin" }), "Role changed").then(() => setDetail(null))}>
          {detail.role === "admin" ? "Demote to student" : "Promote to admin"}</button>
      </Modal>}
    </>
  );
}
