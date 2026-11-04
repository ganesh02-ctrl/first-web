import { Bell, FileWarning, GraduationCap, Users } from "lucide-react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ErrorState, PageHeader, Spinner, Stat } from "../../components/common/ui";
import { useToast } from "../../contexts/ToastContext";
import { useApi } from "../../hooks/useApi";
import { errorMessage, get, send } from "../../services/api";
import { label } from "../../utils/format";

export default function AdminDashboard() {
  const { notify } = useToast();
  const { data, loading, error, reload } = useApi(() => get<any>("/admin/dashboard"));
  const job = async (url: string) => { try { const r = await send<any>("post", url); notify(`Done: ${JSON.stringify(r)}`); reload(); } catch (e) { notify(errorMessage(e), "error"); } };
  if (loading) return <Spinner />;
  if (error || !data) return <ErrorState message={error || "Failed"} onRetry={reload} />;
  const status = Object.entries(data.by_verification_status).map(([k, v]) => ({ name: label(k), count: v }));
  return (
    <>
      <PageHeader title="Admin dashboard" actions={<>
        <button className="btn-secondary" onClick={() => job("/admin/jobs/reminders")}>Run reminders now</button>
        <button className="btn-secondary" onClick={() => job("/admin/jobs/deliveries")}>Process deliveries</button></>} />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Stat icon={<Users />} title="Students (active)" value={`${data.students} (${data.active_students})`} />
        <Stat icon={<GraduationCap />} title="Published / total" value={`${data.scholarships_published} / ${data.scholarships_total}`} />
        <Stat icon={<GraduationCap />} title="Open now" value={data.scholarships_open} />
        <Stat icon={<FileWarning />} title="Open reports" value={data.open_reports} />
      </div>
      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <div className="card"><h2 className="mb-3 font-semibold">Records by verification status</h2>
          {status.length === 0 ? <p className="text-sm text-slate-500">There are no scholarship records yet. Add them from official sources.</p> :
            <ResponsiveContainer width="100%" height={220}><BarChart data={status}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" /><YAxis allowDecimals={false} /><Tooltip /><Bar dataKey="count" fill="#3b5bdb" /></BarChart></ResponsiveContainer>}
        </div>
        <div className="card"><h2 className="mb-3 flex items-center gap-2 font-semibold"><Bell className="h-4 w-4" />Delivery status</h2>
          <table className="table w-full"><tbody>{data.deliveries.map((d: any, i: number) => <tr key={i}><td>{label(d.channel)}</td><td>{label(d.status)}</td><td>{d.count}</td></tr>)}</tbody></table>
          <h3 className="mt-4 font-semibold">Most tracked</h3>
          <ul className="text-sm">{data.most_tracked.map((m: any) => <li key={m.id}>{m.title} — {m.count}</li>)}</ul>
        </div>
      </div>
    </>
  );
}
