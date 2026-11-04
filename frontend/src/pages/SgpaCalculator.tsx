
import { Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import ScalePicker from "../components/academic/ScalePicker";
import { Field, PageHeader, Select, Spinner } from "../components/common/ui";
import { useApi } from "../hooks/useApi";
import { errorMessage, get, send } from "../services/api";
import type { Scale } from "../types";

type Row = { credits: string; grade_label: string };

export default function SgpaCalculator() {
  const { data: scales, loading } = useApi(() => get<Scale[]>("/academics/scales"));

  const [scaleId, setScaleId] = useState("");
  const [rows, setRows] = useState<Row[]>([
    { credits: "", grade_label: "" },
  ]);
  const [result, setResult] = useState<any>(null);
  const [err, setErr] = useState("");

  // Automatically select the shared VTU 2022 template.
  useEffect(() => {
    if (!scales?.length || scaleId) return;

    const defaultScale = scales
      .filter(
        (s) =>
          s.is_template &&
          s.name === "VTU B.E./B.Tech – 2022 Scheme"
      )
      .sort((a, b) => a.id - b.id)[0];

    if (defaultScale) {
      setScaleId(String(defaultScale.id));
    }
  }, [scales, scaleId]);

  const scale = scales?.find((s) => String(s.id) === scaleId);

  const calc = async () => {
    setErr("");
    setResult(null);

    if (!scaleId) {
      setErr("Please select a grading scale.");
      return;
    }

    try {
      setResult(
        await send("post", "/academics/calculate", {
          grading_scale_id: Number(scaleId),
          subjects: rows
            .filter((r) => r.credits && r.grade_label)
            .map((r) => ({
              credits: Number(r.credits),
              grade_label: r.grade_label,
            })),
        })
      );
    } catch (e) {
      setErr(errorMessage(e));
    }
  };

  if (loading) return <Spinner />;

  return (
    <>
      <PageHeader
        title="SGPA Calculator"
        subtitle="SGPA = Σ(credits × grade point) ÷ Σ(credits). To save a semester, use Semester Records."
      />

      <div className="card max-w-3xl space-y-4">
        <Field label="Grading scale">
          <ScalePicker
            scales={scales || []}
            value={scaleId}
            onChange={setScaleId}
          />
        </Field>

        {scale && (
          <>
            {rows.map((r, i) => (
              <div key={i} className="flex gap-2">
                <input
                  className="input"
                  type="number"
                  min={0}
                  step="0.5"
                  placeholder="Credits"
                  value={r.credits}
                  onChange={(e) =>
                    setRows(
                      rows.map((x, j) =>
                        j === i
                          ? { ...x, credits: e.target.value }
                          : x
                      )
                    )
                  }
                />

                <Select
                  value={r.grade_label}
                  placeholder="Grade"
                  options={scale.grades.map((g) => ({
                    value: g.label,
                    label: `${g.label} (${g.grade_point})`,
                  }))}
                  onChange={(v) =>
                    setRows(
                      rows.map((x, j) =>
                        j === i
                          ? { ...x, grade_label: v }
                          : x
                      )
                    )
                  }
                />

                <button
                  className="btn-secondary"
                  onClick={() =>
                    setRows(rows.filter((_, j) => j !== i))
                  }
                  aria-label="Remove"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}

            <div className="flex gap-2">
              <button
                className="btn-secondary"
                onClick={() =>
                  setRows([
                    ...rows,
                    { credits: "", grade_label: "" },
                  ])
                }
              >
                <Plus className="h-4 w-4" />
                Add subject
              </button>

              <button className="btn-primary" onClick={calc}>
                Calculate
              </button>
            </div>
          </>
        )}

        {err && <p className="text-sm text-red-600">{err}</p>}

        {result && (
          <p className="text-lg">
            SGPA: <b>{result.gpa ?? "—"}</b>
            <span className="text-sm text-slate-500">
              {" "}({result.total_credits} credits, out of{" "}
              {scale?.max_grade_point})
            </span>
          </p>
        )}
      </div>
    </>
  );
}
