import { Award, BookMarked, CalendarClock, FileLock2, GraduationCap, Send } from "lucide-react";
import { Link } from "react-router-dom";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Empty, ErrorState, PageHeader, Spinner, Stat } from "../components/common/ui";
import { useApi } from "../hooks/useApi";
import { get } from "../services/api";
import type { Notification, ScholarshipSummary } from "../types";
import { date } from "../utils/format";

interface Dash { tracked_count: number; applications_submitted: number; upcoming_deadlines: ScholarshipSummary[];
  cgpa: number | null; sgpa_trend: { semester: number; sgpa: number | null }[]; achievement_count: number;
  document_count: number; unread_notifications: number; recent_notifications: Notification[]; }

export default function Dashboard() {
  const { data, loading, error, reload } = useApi(() => get<Dash>("/students/me/dashboard"));
  if (loading) return <Spinner />;
  if (error || !data) return <ErrorState message={error || "Failed"} onRetry={reload} />;
  return (
    <>
      <PageHeader title="Dashboard" subtitle="Your activity at a glance" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Stat icon={<BookMarked />} title="Tracked scholarships" value={data.tracked_count} />
        <Stat icon={<Send />} title="Applications submitted" value={data.applications_submitted} />
        <Stat icon={<GraduationCap />} title="CGPA" value={data.cgpa ?? "—"} />
        <Stat icon={<Award />} title="Achievements" value={data.achievement_count} />
        <Stat icon={<FileLock2 />} title="Stored documents" value={data.document_count} />
        <Stat icon={<CalendarClock />} title="Unread notifications" value={data.unread_notifications} />
      </div>
      <div className="mt-6 grid gap-4 lg:grid-cols-2">
        <div className="card"><h2 className="mb-3 font-semibold">Upcoming deadlines</h2>
          {data.upcoming_deadlines.length === 0 ? <p className="text-sm text-slate-500">No upcoming deadlines for scholarships you track. <Link className="text-royal-600" to="/scholarships">Browse scholarships</Link></p> :
            <ul className="space-y-2">{data.upcoming_deadlines.map((s) => (
              <li key={s.id} className="flex justify-between text-sm"><Link className="text-royal-600" to={`/scholarships/${s.id}`}>{s.title}</Link>
                <span>{date(s.application_close_date)} ({s.days_left}d)</span></li>))}</ul>}
        </div>
        <div className="card"><h2 className="mb-3 font-semibold">SGPA trend</h2>
          {data.sgpa_trend.length === 0 ? <p className="text-sm text-slate-500">You haven't added any semesters yet.</p> :
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={data.sgpa_trend}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="semester" /><YAxis /><Tooltip />
                <Line type="monotone" dataKey="sgpa" stroke="#3b5bdb" strokeWidth={2} /></LineChart>
            </ResponsiveContainer>}
        </div>
      </div>
      <div className="card mt-6"><h2 className="mb-3 font-semibold">Recent notifications</h2>
        {data.recent_notifications.length === 0 ? <Empty title="No notifications yet" /> :
          <ul className="space-y-2">{data.recent_notifications.map((n) => <li key={n.id} className="text-sm"><b>{n.title}</b> — {n.message}</li>)}</ul>}
      </div>
    </>
  );
}
