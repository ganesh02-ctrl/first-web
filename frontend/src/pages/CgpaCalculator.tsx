import { Download } from "lucide-react";
import { Link } from "react-router-dom";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Empty, ErrorState, PageHeader, Spinner, Stat } from "../components/common/ui";
import { useApi } from "../hooks/useApi";
import { get, openFile } from "../services/api";
import type { Semester } from "../types";
import { GraduationCap, Layers } from "lucide-react";

export default function CgpaCalculator() {
  const { data, loading, error, reload } = useApi(() => get<{ cgpa: number | null; total_credits: number; semester_count: number;
    mixed_scales: boolean; max_grade_point: number | null; semesters: Semester[] }>("/academics/summary"));
  if (loading) return <Spinner />;
  if (error || !data) return <ErrorState message={error || "Failed"} onRetry={reload} />;
  return (
    <>
      <PageHeader title="CGPA" subtitle="CGPA = Σ(credits × grade point) across every subject in every semester. It is not an average of your SGPAs."
        actions={<button className="btn-secondary" onClick={() => openFile("/academics/report.pdf", "academic-report.pdf")}><Download className="h-4 w-4" />PDF report</button>} />
      {data.semester_count === 0 ? <Empty title="No semesters recorded" action={<Link className="btn-primary" to="/semesters">Add semesters</Link>} /> : <>
        <div className="grid gap-4 md:grid-cols-3">
          <Stat icon={<GraduationCap />} title="CGPA" value={`${data.cgpa ?? "—"}${data.max_grade_point ? ` / ${data.max_grade_point}` : ""}`} />
          <Stat icon={<Layers />} title="Total credits" value={data.total_credits} />
          <Stat icon={<Layers />} title="Semesters" value={data.semester_count} />
        </div>
        {data.mixed_scales && <p className="mt-3 rounded bg-amber-50 p-3 text-sm text-amber-800">Your semesters use different grading scales, so this CGPA combines incompatible scales. Treat it with caution.</p>}
        <div className="card mt-6"><h2 className="mb-3 font-semibold">SGPA by semester</h2>
          <ResponsiveContainer width="100%" height={260}><BarChart data={data.semesters.map((s) => ({ name: `S${s.number}`, sgpa: s.sgpa }))}>
            <CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="name" /><YAxis /><Tooltip /><Bar dataKey="sgpa" fill="#7c5cd6" radius={[4, 4, 0, 0]} /></BarChart></ResponsiveContainer>
        </div></>}
    </>
  );
}
