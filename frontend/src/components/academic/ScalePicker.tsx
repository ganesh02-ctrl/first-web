import { Link } from "react-router-dom";
import { Select } from "../common/ui";
import type { Scale } from "../../types";

export default function ScalePicker({ scales, value, onChange }: { scales: Scale[]; value: number | string | null; onChange(v: string): void }) {
  if (scales.length === 0)
    return <p className="text-sm text-slate-500">You don't have a grading scale yet. <Link className="text-royal-600" to="/settings">Add your university's scale in Settings</Link>.</p>;
  return <Select value={value} onChange={onChange} placeholder="Select grading scale"
    options={scales.map((s) => ({ value: s.id, label: `${s.name}${s.is_template ? " (shared)" : ""}` }))} />;
}
