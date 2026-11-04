import { useState } from "react";
import ScholarshipCard from "../components/scholarship/ScholarshipCard";
import { Empty, ErrorState, Field, PageHeader, Pager, Select, Spinner } from "../components/common/ui";
import { useApi } from "../hooks/useApi";
import { useVocab } from "../hooks/useVocab";
import { get, getPage } from "../services/api";
import type { Category, ScholarshipSummary } from "../types";

const initial = { q: "", state: "", category_id: "", education_level: "", scholarship_type: "", income: "",
  deadline_before: "", include_expired: "", sort: "deadline" };

export default function Scholarships() {
  const vocab = useVocab();
  const cats = useApi(() => get<Category[]>("/scholarships/categories")).data || [];
  const [f, setF] = useState(initial); const [applied, setApplied] = useState(initial); const [page, setPage] = useState(1);
  const params = Object.fromEntries(Object.entries({ ...applied, page }).filter(([, v]) => v !== ""));
  const { data, loading, error, reload } = useApi(() => getPage<ScholarshipSummary>("/scholarships", params), [JSON.stringify(params)]);
  const set = (k: keyof typeof f) => (v: string) => setF({ ...f, [k]: v });

  return (
    <>
      <PageHeader title="Scholarship Hub" subtitle="Admins check every record against its official source. Confirm the details on the official portal before you apply." />
      <form className="card mb-6 grid gap-3 md:grid-cols-4" onSubmit={(e) => { e.preventDefault(); setPage(1); setApplied(f); }}>
        <Field label="Search"><input className="input" value={f.q} onChange={(e) => set("q")(e.target.value)} placeholder="Title, provider…" /></Field>
        <Field label="State"><Select value={f.state} onChange={set("state")} options={vocab?.states || []} placeholder="Any" /></Field>
        <Field label="Category"><Select value={f.category_id} onChange={set("category_id")} options={cats.map((c) => ({ value: c.id, label: c.name }))} placeholder="Any" /></Field>
        <Field label="Education level"><Select value={f.education_level} onChange={set("education_level")} options={vocab?.education_levels || []} placeholder="Any" /></Field>
        <Field label="Type"><Select value={f.scholarship_type} onChange={set("scholarship_type")} options={vocab?.scholarship_types || []} placeholder="Any" /></Field>
        <Field label="Family income (₹/yr)"><input className="input" type="number" min={0} value={f.income} onChange={(e) => set("income")(e.target.value)} /></Field>
        <Field label="Deadline before"><input className="input" type="date" value={f.deadline_before} onChange={(e) => set("deadline_before")(e.target.value)} /></Field>
        <Field label="Sort"><Select value={f.sort} onChange={set("sort")} options={[{ value: "deadline", label: "Deadline" }, { value: "newest", label: "Newest" }, { value: "title", label: "Title" }]} /></Field>
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={f.include_expired === "true"} onChange={(e) => set("include_expired")(e.target.checked ? "true" : "")} />Include expired</label>
        <div className="flex gap-2 md:col-span-3 md:justify-end">
          <button type="button" className="btn-secondary" onClick={() => { setF(initial); setApplied(initial); }}>Reset</button>
          <button className="btn-primary">Apply filters</button></div>
      </form>
      {loading ? <Spinner /> : error ? <ErrorState message={error} onRetry={reload} /> :
        data!.items.length === 0 ? <Empty title="No scholarships found" text="Nothing matches these filters, or an administrator hasn't published any verified records yet." /> :
          <><div className="grid gap-4 md:grid-cols-2">{data!.items.map((s) => <ScholarshipCard key={s.id} s={s} />)}</div>
            <Pager page={data!.meta.page} pages={data!.meta.pages} onPage={setPage} /></>}
    </>
  );
}
