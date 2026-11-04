import { Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Badge, Field, PageHeader, Select, Spinner } from "../../components/common/ui";
import { useToast } from "../../contexts/ToastContext";
import { useApi } from "../../hooks/useApi";
import { useVocab } from "../../hooks/useVocab";
import { errorMessage, get, send } from "../../services/api";
import type { Category, ScholarshipDetail } from "../../types";
import { date } from "../../utils/format";

const blank: any = { title: "", provider_name: "", provider_type: "central_government", scholarship_type: "merit", category_id: "", state: "",
  academic_year: "", description: "", benefits: "", amount_text: "", amount_max: "", application_open_date: "", application_close_date: "",
  official_source_name: "", source_url: "", application_url: "", verification_notes: "", eligibility: [], required_documents: [] };
const TEXT = ["title", "provider_name", "official_source_name", "source_url", "application_url", "academic_year", "amount_text"];

export default function AdminScholarshipForm() {
  const { id } = useParams(); const nav = useNavigate(); const vocab = useVocab(); const { notify } = useToast();
  const cats = useApi(() => get<Category[]>("/admin/categories")).data || [];
  const [f, setF] = useState<any>(id ? null : blank); const [rec, setRec] = useState<ScholarshipDetail | null>(null);
  const load = () => id && get<ScholarshipDetail>(`/admin/scholarships/${id}`).then((s) => { setRec(s);
    setF({ ...blank, ...Object.fromEntries(Object.keys(blank).map((k) => [k, (s as any)[k] ?? ""])), category_id: s.category?.id ?? "" }); });
  useEffect(() => { load(); }, [id]); // eslint-disable-line react-hooks/exhaustive-deps
  if (!f) return <Spinner />;
  const set = (k: string) => (v: any) => setF({ ...f, [k]: v });
  const listSet = (k: string, i: number, field: string, v: any) => set(k)(f[k].map((x: any, j: number) => (j === i ? { ...x, [field]: v } : x)));

  const save = async () => {
    const body: any = {};
    Object.keys(blank).forEach((k) => (body[k] = f[k] === "" ? null : f[k]));
    body.category_id = f.category_id ? Number(f.category_id) : null; body.amount_max = f.amount_max === "" ? null : Number(f.amount_max);
    body.eligibility = f.eligibility.map((e: any) => ({ criterion_type: e.criterion_type, description: e.description, value: e.value || null,
      numeric_value: e.numeric_value === "" || e.numeric_value == null ? null : Number(e.numeric_value) }));
    body.required_documents = f.required_documents.map((d: any) => ({ document_type: d.document_type, name: d.name, is_mandatory: d.is_mandatory, notes: d.notes || null }));
    try { const s = await send<ScholarshipDetail>(id ? "patch" : "post", id ? `/admin/scholarships/${id}` : "/admin/scholarships", body);
      notify("Saved"); if (!id) nav(`/admin/scholarships/${s.id}`); else load(); } catch (e) { notify(errorMessage(e), "error"); }
  };
  const act = async (url: string, body: any, ok: string) => { try { await send(url.includes("verify") ? "post" : "patch", url, body); notify(ok); load(); } catch (e) { notify(errorMessage(e), "error"); } };

  return (
    <>
      <PageHeader title={id ? "Edit scholarship" : "New scholarship"} actions={rec && <><Badge value={rec.effective_status} /><span className="text-sm">{rec.is_published ? "Published" : "Not published"}</span></>} />
      {rec && <div className="card mb-4 space-y-2 text-sm">
        <p>Last verified: {date(rec.last_verified_at)} {(rec as any).verified_by && `by ${(rec as any).verified_by}`}</p>
        {rec.publish_problems?.length ? <ul className="list-disc pl-5 text-amber-700">{rec.publish_problems.map((p) => <li key={p}>{p}</li>)}</ul> : null}
        <div className="flex flex-wrap gap-2">
          <button className="btn-secondary" onClick={() => act(`/admin/scholarships/${id}/verify`, { verification_status: "verified", verification_notes: f.verification_notes || null }, "Marked verified")}>I checked the official source: mark verified</button>
          <button className="btn-secondary" onClick={() => act(`/admin/scholarships/${id}/verify`, { verification_status: "needs_review" }, "Marked needs review")}>Needs review</button>
          <button className="btn-primary" onClick={() => act(`/admin/scholarships/${id}`, { is_published: !rec.is_published }, "Publish state changed")}>{rec.is_published ? "Unpublish" : "Publish"}</button>
        </div></div>}
      <div className="card grid gap-3 md:grid-cols-2">
        {TEXT.map((k) => <Field key={k} label={k.replace(/_/g, " ")}><input className="input" value={f[k]} onChange={(e) => set(k)(e.target.value)} /></Field>)}
        <Field label="Provider type"><Select value={f.provider_type} onChange={set("provider_type")} options={vocab?.provider_types || []} /></Field>
        <Field label="Scholarship type"><Select value={f.scholarship_type} onChange={set("scholarship_type")} options={vocab?.scholarship_types || []} /></Field>
        <Field label="Category"><Select value={f.category_id} onChange={set("category_id")} placeholder="None" options={cats.map((c) => ({ value: c.id, label: c.name }))} /></Field>
        <Field label="State (empty = all India)"><Select value={f.state} onChange={set("state")} placeholder="All India" options={vocab?.states || []} /></Field>
        <Field label="Max amount (₹)"><input className="input" type="number" value={f.amount_max} onChange={(e) => set("amount_max")(e.target.value)} /></Field>
        <Field label="Opens"><input className="input" type="date" value={f.application_open_date} onChange={(e) => set("application_open_date")(e.target.value)} /></Field>
        <Field label="Closes (deadline)"><input className="input" type="date" value={f.application_close_date} onChange={(e) => set("application_close_date")(e.target.value)} /></Field>
        {["description", "benefits", "verification_notes"].map((k) => <div key={k} className="md:col-span-2"><Field label={k.replace(/_/g, " ")}><textarea className="input" rows={3} value={f[k]} onChange={(e) => set(k)(e.target.value)} /></Field></div>)}
      </div>
      <div className="card mt-4 space-y-2"><h2 className="font-semibold">Eligibility criteria</h2>
        {f.eligibility.map((e: any, i: number) => <div key={i} className="grid gap-2 md:grid-cols-[150px_140px_120px_1fr_auto]">
          <Select value={e.criterion_type} onChange={(v) => listSet("eligibility", i, "criterion_type", v)} options={vocab?.eligibility_criteria || []} />
          <input className="input" placeholder="value (e.g. undergraduate)" value={e.value || ""} onChange={(x) => listSet("eligibility", i, "value", x.target.value)} />
          <input className="input" type="number" placeholder="number (e.g. income cap)" value={e.numeric_value ?? ""} onChange={(x) => listSet("eligibility", i, "numeric_value", x.target.value)} />
          <input className="input" placeholder="Description as stated by the official source" value={e.description} onChange={(x) => listSet("eligibility", i, "description", x.target.value)} />
          <button className="btn-secondary" onClick={() => set("eligibility")(f.eligibility.filter((_: any, j: number) => j !== i))} aria-label="Remove"><Trash2 className="h-4 w-4" /></button></div>)}
        <button className="btn-secondary" onClick={() => set("eligibility")([...f.eligibility, { criterion_type: "education_level", value: "", numeric_value: "", description: "" }])}><Plus className="h-4 w-4" />Add criterion</button>
      </div>
      <div className="card mt-4 space-y-2"><h2 className="font-semibold">Required documents</h2>
        {f.required_documents.map((d: any, i: number) => <div key={i} className="grid gap-2 md:grid-cols-[200px_1fr_auto_auto]">
          <Select value={d.document_type} onChange={(v) => listSet("required_documents", i, "document_type", v)} options={Object.entries(vocab?.document_types || {}).map(([value, label]) => ({ value, label }))} />
          <input className="input" placeholder="Name" value={d.name} onChange={(x) => listSet("required_documents", i, "name", x.target.value)} />
          <label className="flex items-center gap-1 text-sm"><input type="checkbox" checked={d.is_mandatory} onChange={(x) => listSet("required_documents", i, "is_mandatory", x.target.checked)} />Mandatory</label>
          <button className="btn-secondary" onClick={() => set("required_documents")(f.required_documents.filter((_: any, j: number) => j !== i))} aria-label="Remove"><Trash2 className="h-4 w-4" /></button></div>)}
        <button className="btn-secondary" onClick={() => set("required_documents")([...f.required_documents, { document_type: "other", name: "", is_mandatory: true }])}><Plus className="h-4 w-4" />Add document</button>
      </div>
      <div className="mt-4 flex justify-end gap-2"><button className="btn-secondary" onClick={() => nav("/admin/scholarships")}>Back</button><button className="btn-primary" onClick={save}>Save</button></div>
      <p className="mt-2 text-right text-xs text-slate-500">Changing the deadline, links, amount or eligibility on a verified record sends it back to "needs review" and unpublishes it.</p>
    </>
  );
}
