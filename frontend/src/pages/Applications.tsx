import { useState } from "react";
import { Link } from "react-router-dom";
import { Badge, Empty, ErrorState, Field, Modal, PageHeader, Select, Spinner } from "../components/common/ui";
import { useToast } from "../contexts/ToastContext";
import { useApi } from "../hooks/useApi";
import { useVocab } from "../hooks/useVocab";
import { errorMessage, get, send } from "../services/api";
import type { Application } from "../types";
import { clean, date } from "../utils/format";

export default function Applications() {
  const vocab = useVocab(); const { notify } = useToast();
  const [status, setStatus] = useState("");
  const { data, loading, error, reload } = useApi(() => get<Application[]>("/applications", status ? { status } : {}), [status]);
  const [edit, setEdit] = useState<Application | null>(null);
  const [f, setF] = useState<any>({});
  const open = (a: Application) => { setEdit(a); setF({ status: a.status, applied_on: a.applied_on || "", application_reference: a.application_reference || "", notes: a.notes || "", status_note: "" }); };
  const save = async () => {
    try { await send("put", `/applications/${edit!.scholarship_id}`, clean(f)); notify("Saved"); setEdit(null); reload(); } catch (e) { notify(errorMessage(e), "error"); }
  };
  const remove = async (a: Application) => {
    if (!confirm("Delete this application record?")) return;
    try { await send("delete", `/applications/${a.scholarship_id}`); reload(); } catch (e) { notify(errorMessage(e), "error"); }
  };
  return (
    <>
      <PageHeader title="Application tracking" actions={<div className="w-48"><Select value={status} onChange={setStatus} options={vocab?.application_statuses || []} placeholder="All statuses" /></div>} />
      {loading ? <Spinner /> : error ? <ErrorState message={error} onRetry={reload} /> : data!.length === 0 ?
        <Empty title="No applications yet" text="Open a scholarship and set your application status there." /> :
        <div className="card overflow-x-auto"><table className="table w-full"><thead><tr><th>Scholarship</th><th>Status</th><th>Applied on</th><th>Reference</th><th /></tr></thead>
          <tbody>{data!.map((a) => <tr key={a.id}>
            <td><Link className="text-royal-600" to={`/scholarships/${a.scholarship_id}`}>{a.scholarship?.title}</Link></td>
            <td><Badge value={a.status} text={a.status_label} /></td><td>{date(a.applied_on)}</td><td>{a.application_reference || "—"}</td>
            <td className="space-x-3 text-sm"><button className="text-royal-600" onClick={() => open(a)}>Edit</button><button className="text-red-600" onClick={() => remove(a)}>Delete</button></td></tr>)}</tbody></table></div>}
      {edit && <Modal title={edit.scholarship?.title || "Application"} onClose={() => setEdit(null)}>
        <div className="grid gap-3 md:grid-cols-2">
          <Field label="Status"><Select value={f.status} onChange={(v) => setF({ ...f, status: v })} options={vocab?.application_statuses || []} /></Field>
          <Field label="Applied on"><input className="input" type="date" value={f.applied_on} onChange={(e) => setF({ ...f, applied_on: e.target.value })} /></Field>
          <Field label="Application reference"><input className="input" value={f.application_reference} onChange={(e) => setF({ ...f, application_reference: e.target.value })} /></Field>
          <Field label="Status note"><input className="input" value={f.status_note} onChange={(e) => setF({ ...f, status_note: e.target.value })} /></Field>
          <div className="md:col-span-2"><Field label="Notes"><textarea className="input" rows={3} value={f.notes} onChange={(e) => setF({ ...f, notes: e.target.value })} /></Field></div>
        </div>
        <h3 className="mt-4 text-sm font-semibold">History</h3>
        <ul className="text-xs text-slate-500">{edit.history?.map((h, i) => <li key={i}>{date(h.changed_at)}: {h.to_status_label}{h.note ? ` — ${h.note}` : ""}</li>)}</ul>
        <button className="btn-primary mt-4" onClick={save}>Save</button>
      </Modal>}
    </>
  );
}
