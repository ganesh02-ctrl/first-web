import { Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { Field } from "../common/ui";
import type { Scale } from "../../types";

export type ScaleInput = { name: string; description: string; max_grade_point: string; as_template?: boolean;
  grades: { label: string; grade_point: string; counts_in_gpa: boolean }[] };

export default function ScaleEditor({ initial, allowTemplate, onSave }: { initial?: Scale; allowTemplate?: boolean; onSave(d: any): void }) {
  const [f, setF] = useState<ScaleInput>(initial ? { name: initial.name, description: initial.description || "", max_grade_point: String(initial.max_grade_point),
    grades: initial.grades.map((g) => ({ label: g.label, grade_point: String(g.grade_point), counts_in_gpa: g.counts_in_gpa })) }
    : { name: "", description: "", max_grade_point: "10", grades: [{ label: "", grade_point: "", counts_in_gpa: true }] });
  const setG = (i: number, k: string, v: any) => setF({ ...f, grades: f.grades.map((g, j) => (j === i ? { ...g, [k]: v } : g)) });
  return (
    <div className="space-y-3">
      <p className="text-xs text-slate-500">Copy the grades and grade points exactly as they appear in your university's official regulations.</p>
      <div className="grid gap-3 md:grid-cols-2">
        <Field label="Name"><input className="input" value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} /></Field>
        <Field label="Maximum grade point"><input className="input" type="number" value={f.max_grade_point} onChange={(e) => setF({ ...f, max_grade_point: e.target.value })} /></Field>
      </div>
      {f.grades.map((g, i) => (
        <div key={i} className="flex items-center gap-2">
          <input className="input" placeholder="Label (e.g. O)" value={g.label} onChange={(e) => setG(i, "label", e.target.value)} />
          <input className="input" type="number" step="0.01" placeholder="Grade point" value={g.grade_point} onChange={(e) => setG(i, "grade_point", e.target.value)} />
          <label className="flex shrink-0 items-center gap-1 text-xs"><input type="checkbox" checked={g.counts_in_gpa} onChange={(e) => setG(i, "counts_in_gpa", e.target.checked)} />In GPA</label>
          <button className="btn-secondary" onClick={() => setF({ ...f, grades: f.grades.filter((_, j) => j !== i) })} aria-label="Remove"><Trash2 className="h-4 w-4" /></button>
        </div>))}
      <button className="btn-secondary" onClick={() => setF({ ...f, grades: [...f.grades, { label: "", grade_point: "", counts_in_gpa: true }] })}><Plus className="h-4 w-4" />Add grade</button>
      {allowTemplate && !initial && <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={!!f.as_template} onChange={(e) => setF({ ...f, as_template: e.target.checked })} />Shared template for all students</label>}
      <button className="btn-primary" onClick={() => onSave({ name: f.name, description: f.description || null, max_grade_point: Number(f.max_grade_point), as_template: f.as_template,
        grades: f.grades.map((g, i) => ({ label: g.label, grade_point: Number(g.grade_point), counts_in_gpa: g.counts_in_gpa, sort_order: i })) })}>Save scale</button>
    </div>
  );
}
