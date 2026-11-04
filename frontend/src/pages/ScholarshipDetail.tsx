import { Bookmark, ExternalLink, Flag } from "lucide-react";
import { useState } from "react";
import { useParams } from "react-router-dom";
import { Badge, ErrorState, Field, Modal, PageHeader, Select, Spinner } from "../components/common/ui";
import { useAuth } from "../contexts/AuthContext";
import { useToast } from "../contexts/ToastContext";
import { useApi } from "../hooks/useApi";
import { useVocab } from "../hooks/useVocab";
import { errorMessage, get, send } from "../services/api";
import type { ScholarshipDetail as SD } from "../types";
import { date, inr, label } from "../utils/format";

export default function ScholarshipDetail() {
  const { id } = useParams(); const { user } = useAuth(); const { notify } = useToast(); const vocab = useVocab();
  const { data: s, loading, error, reload } = useApi(() => get<SD>(`/scholarships/${id}`), [id]);
  const checklist = useApi(() => (user?.role === "student" && s ? get<any>("/documents/checklist", { scholarship_id: s.id }) : Promise.resolve(null)), [s?.id]);
  const [report, setReport] = useState(false); const [r, setR] = useState({ reason: "wrong_deadline", details: "" });
  const isStudent = user?.role === "student";

  const act = async (fn: () => Promise<unknown>, ok: string) => { try { await fn(); notify(ok); reload(); } catch (e) { notify(errorMessage(e), "error"); } };
  if (loading) return <Spinner />;
  if (error || !s) return <ErrorState message={error || "Not found"} />;
  const expired = s.effective_status === "expired";

  return (
    <>
      <PageHeader title={s.title} subtitle={s.provider_name} actions={<>
        <Badge value={s.effective_status} />
        <a className="btn-primary" href={s.application_url} target="_blank" rel="noopener noreferrer"><ExternalLink className="h-4 w-4" />Official application</a>
      </>} />
      {expired && <div className="mb-4 rounded-lg bg-slate-100 p-3 text-sm dark:bg-slate-800">The deadline for this record has passed. Check the official source for the next cycle.</div>}
      <div className="grid gap-4 lg:grid-cols-3">
        <div className="space-y-4 lg:col-span-2">
          <div className="card space-y-2 text-sm">
            <p>{s.description || "No description provided."}</p>
            <p><b>Benefits:</b> {s.benefits || s.amount_text || "See official source"} {s.amount_max ? `(up to ${inr(s.amount_max)})` : ""}</p>
            <p><b>Opens:</b> {date(s.application_open_date)} · <b>Closes:</b> {date(s.application_close_date)}</p>
            <p><b>Type:</b> {label(s.scholarship_type)} · <b>State:</b> {s.state || "All India"} · <b>Year:</b> {s.academic_year || "—"}</p>
          </div>
          <div className="card"><h2 className="mb-2 font-semibold">Eligibility</h2>
            <ul className="list-disc space-y-1 pl-5 text-sm">{s.eligibility.map((e) => <li key={e.id}>{e.description}</li>)}</ul></div>
          <div className="card"><h2 className="mb-2 font-semibold">Required documents</h2>
            {s.required_documents.length === 0 ? <p className="text-sm text-slate-500">This record doesn't list any documents.</p> :
              <ul className="space-y-1 text-sm">{s.required_documents.map((d) => {
                const have = checklist.data?.items?.find((i: any) => i.document_type === d.document_type)?.available;
                return <li key={d.id}>{isStudent && (have ? "✅ " : "⬜ ")}{d.name}{d.is_mandatory ? "" : " (optional)"}{d.notes ? ` — ${d.notes}` : ""}</li>;
              })}</ul>}
          </div>
          <div className="card text-xs text-slate-500">
            Source: <a className="text-royal-600" href={s.source_url} target="_blank" rel="noopener noreferrer">{s.official_source_name}</a> · Last verified {date(s.last_verified_at)}
            {s.verification_notes && <p className="mt-1">Notes: {s.verification_notes}</p>}
          </div>
        </div>
        {isStudent && (
          <div className="space-y-4">
            <div className="card space-y-3">
              <h2 className="font-semibold">Track</h2>
              {s.tracking ? <>
                <button className="btn-secondary w-full" onClick={() => act(() => send("put", `/tracking/${s.id}`, { is_bookmarked: !s.tracking!.is_bookmarked }), "Updated")}>
                  <Bookmark className="h-4 w-4" />{s.tracking.is_bookmarked ? "Remove bookmark" : "Bookmark"}</button>
                <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={s.tracking.reminders_enabled}
                  onChange={(e) => act(() => send("put", `/tracking/${s.id}`, { reminders_enabled: e.target.checked }), "Reminder setting saved")} />Deadline reminders</label>
                <button className="btn-secondary w-full" onClick={() => act(() => send("delete", `/tracking/${s.id}`), "Untracked")}>Stop tracking</button>
              </> : <button className="btn-primary w-full" disabled={expired} onClick={() => act(() => send("put", `/tracking/${s.id}`, {}), "Tracking started")}>Track this scholarship</button>}
            </div>
            <div className="card space-y-2"><h2 className="font-semibold">My application status</h2>
              <Select value={s.application?.status || ""} placeholder="Not started" options={vocab?.application_statuses || []}
                onChange={(v) => v && act(() => send("put", `/applications/${s.id}`, { status: v }), "Status saved")} />
            </div>
            <button className="btn-secondary w-full" onClick={() => setReport(true)}><Flag className="h-4 w-4" />Report incorrect info</button>
          </div>)}
      </div>
      {report && <Modal title="Report incorrect information" onClose={() => setReport(false)}>
        <div className="space-y-3">
          <Field label="Reason"><Select value={r.reason} onChange={(v) => setR({ ...r, reason: v })} options={vocab?.report_reasons || []} /></Field>
          <Field label="Details (at least 10 characters)"><textarea className="input" rows={4} value={r.details} onChange={(e) => setR({ ...r, details: e.target.value })} /></Field>
          <button className="btn-primary" onClick={() => act(() => send("post", `/scholarships/${s.id}/report`, r), "Report submitted").then(() => setReport(false))}>Submit</button>
        </div></Modal>}
    </>
  );
}
