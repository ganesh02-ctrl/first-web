import { FormEvent, useEffect, useState } from "react";
import { ErrorState, Field, PageHeader, Select, Spinner } from "../components/common/ui";
import { useAuth } from "../contexts/AuthContext";
import { useToast } from "../contexts/ToastContext";
import { useApi } from "../hooks/useApi";
import { useVocab } from "../hooks/useVocab";
import { errorMessage, get, send } from "../services/api";
import { label } from "../utils/format";

const TEXT = ["full_name", "phone", "gender", "district", "college", "university", "degree", "branch", "social_category"];

export default function Profile() {
  const vocab = useVocab(); const { notify } = useToast(); const { reload: reloadUser } = useAuth();
  const { data, loading, error, reload } = useApi(() => get<any>("/students/me/profile"));
  const [f, setF] = useState<any>(null);
  useEffect(() => { if (data) setF(Object.fromEntries(Object.entries(data).map(([k, v]) => [k, v ?? ""]))); }, [data]);
  if (loading || (!f && !error)) return <Spinner />;
  if (error) return <ErrorState message={error} onRetry={reload} />;
  const set = (k: string) => (v: any) => setF({ ...f, [k]: v });
  const toggle = (k: string, v: string) => set(k)(f[k].includes(v) ? f[k].filter((x: string) => x !== v) : [...f[k], v]);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const body: any = {};
    [...TEXT, "date_of_birth", "state", "education_level", "academic_summary"].forEach((k) => (body[k] = f[k] === "" ? null : f[k]));
    body.full_name = f.full_name;
    ["current_semester", "graduation_year", "annual_family_income"].forEach((k) => (body[k] = f[k] === "" ? null : Number(f[k])));
    body.preferred_scholarship_types = f.preferred_scholarship_types; body.preferred_states = f.preferred_states;
    try { await send("patch", "/students/me/profile", body); notify("Profile saved"); reload(); reloadUser(); } catch (x) { notify(errorMessage(x), "error"); }
  };
  return (
    <>
      <PageHeader title="Student profile" subtitle={data.email} />
      <form onSubmit={submit} className="card grid gap-3 md:grid-cols-3">
        {TEXT.map((k) => <Field key={k} label={label(k)}><input className="input" value={f[k]} onChange={(e) => set(k)(e.target.value)} required={k === "full_name"} /></Field>)}
        <Field label="Date of birth"><input className="input" type="date" value={f.date_of_birth} onChange={(e) => set("date_of_birth")(e.target.value)} /></Field>
        <Field label="State"><Select value={f.state} onChange={set("state")} options={vocab?.states || []} placeholder="—" /></Field>
        <Field label="Education level"><Select value={f.education_level} onChange={set("education_level")} options={vocab?.education_levels || []} placeholder="—" /></Field>
        <Field label="Current semester"><input className="input" type="number" min={1} max={20} value={f.current_semester} onChange={(e) => set("current_semester")(e.target.value)} /></Field>
        <Field label="Graduation year"><input className="input" type="number" value={f.graduation_year} onChange={(e) => set("graduation_year")(e.target.value)} /></Field>
        <Field label="Annual family income (₹)"><input className="input" type="number" min={0} value={f.annual_family_income} onChange={(e) => set("annual_family_income")(e.target.value)} /></Field>
        <div className="md:col-span-3"><Field label="Academic information"><textarea className="input" rows={3} value={f.academic_summary} onChange={(e) => set("academic_summary")(e.target.value)} /></Field></div>
        <div className="md:col-span-3"><span className="label">Preferred scholarship types</span><div className="flex flex-wrap gap-2">
          {vocab?.scholarship_types.map((t) => <label key={t} className="flex items-center gap-1 text-sm"><input type="checkbox" checked={f.preferred_scholarship_types.includes(t)} onChange={() => toggle("preferred_scholarship_types", t)} />{label(t)}</label>)}</div></div>
        <div className="md:col-span-3"><span className="label">Preferred states</span><div className="flex max-h-32 flex-wrap gap-2 overflow-y-auto">
          {vocab?.states.map((t) => <label key={t} className="flex items-center gap-1 text-sm"><input type="checkbox" checked={f.preferred_states.includes(t)} onChange={() => toggle("preferred_states", t)} />{t}</label>)}</div></div>
        <div className="md:col-span-3 flex justify-end"><button className="btn-primary">Save profile</button></div>
      </form>
    </>
  );
}
