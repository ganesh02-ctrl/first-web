
import { Plus, Trash2 } from "lucide-react";
import { useEffect, useState } from "react";
import ScalePicker from "../components/academic/ScalePicker";
import {
  Empty,
  ErrorState,
  Field,
  Modal,
  PageHeader,
  Select,
  Spinner,
} from "../components/common/ui";
import { useToast } from "../contexts/ToastContext";
import { useApi } from "../hooks/useApi";
import { errorMessage, get, send } from "../services/api";
import type { Scale, Semester } from "../types";
import { clean } from "../utils/format";

const DEFAULT_SCALE_NAME = "VTU B.E./B.Tech – 2022 Scheme";

export default function Semesters() {
  const { notify } = useToast();

  const scales = useApi(() => get<Scale[]>("/academics/scales")).data || [];
  const { data, loading, error, reload } = useApi(
    () => get<Semester[]>("/academics/semesters")
  );

  const [semForm, setSemForm] = useState<any>(null);

  const [sub, setSub] = useState<
    Record<
      number,
      { name: string; code: string; credits: string; grade_label: string }
    >
  >({});

  // Automatically select the shared 2022 scheme for new semesters.
  useEffect(() => {
    if (!semForm || semForm.id || semForm.grading_scale_id || !scales.length) {
      return;
    }

    const defaultScale = scales
      .filter(
        (s) => s.is_template && s.name === DEFAULT_SCALE_NAME
      )
      .sort((a, b) => a.id - b.id)[0];

    if (defaultScale) {
      setSemForm((current: any) =>
        current && !current.id && !current.grading_scale_id
          ? { ...current, grading_scale_id: String(defaultScale.id) }
          : current
      );
    }
  }, [scales, semForm]);

  const run = async (fn: () => Promise<unknown>, ok: string) => {
    try {
      await fn();
      notify(ok);
      reload();
      return true;
    } catch (e) {
      notify(errorMessage(e), "error");
      return false;
    }
  };

  const saveSem = async () => {
    const body = clean({
      ...semForm,
      number: Number(semForm.number),
      grading_scale_id: Number(semForm.grading_scale_id),
    });

    delete (body as any).id;

    if (
      await run(
        () =>
          semForm.id
            ? send("put", `/academics/semesters/${semForm.id}`, body)
            : send("post", "/academics/semesters", body),
        "Semester saved"
      )
    ) {
      setSemForm(null);
    }
  };

  if (loading) return <Spinner />;
  if (error) return <ErrorState message={error} onRetry={reload} />;

  return (
    <>
      <PageHeader
        title="Semester records"
        actions={
          <button
            className="btn-primary"
            onClick={() =>
              setSemForm({
                number: (data?.length || 0) + 1,
                title: "",
                academic_year: "",
                grading_scale_id: "",
              })
            }
          >
            <Plus className="h-4 w-4" />
            Add semester
          </button>
        }
      />

      {data!.length === 0 ? (
        <Empty
          title="No semesters yet"
          text="Add a semester, choose your university's grading scale, then add subjects."
        />
      ) : (
        <div className="space-y-4">
          {data!.map((s) => {
            const scale = scales.find(
              (x) => x.id === s.grading_scale_id
            );

            const f = sub[s.id] || {
              name: "",
              code: "",
              credits: "",
              grade_label: "",
            };

            const setF = (k: string, v: string) =>
              setSub({
                ...sub,
                [s.id]: { ...f, [k]: v },
              });

            return (
              <div key={s.id} className="card">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <h2 className="font-semibold">
                      {s.title}{" "}
                      {s.academic_year && (
                        <span className="text-sm text-slate-500">
                          ({s.academic_year})
                        </span>
                      )}
                    </h2>
                    <p className="text-sm text-slate-500">
                      SGPA <b>{s.sgpa ?? "—"}</b> · {s.total_credits} credits ·{" "}
                      {s.grading_scale_name || "No scale"}
                    </p>
                  </div>

                  <div className="space-x-3 text-sm">
                    <button
                      className="text-royal-600"
                      onClick={() =>
                        setSemForm({
                          id: s.id,
                          number: s.number,
                          title: s.title,
                          academic_year: s.academic_year || "",
                          grading_scale_id: s.grading_scale_id || "",
                        })
                      }
                    >
                      Edit
                    </button>

                    <button
                      className="text-red-600"
                      onClick={() =>
                        confirm("Delete this semester and its subjects?") &&
                        run(
                          () =>
                            send("delete", `/academics/semesters/${s.id}`),
                          "Deleted"
                        )
                      }
                    >
                      Delete
                    </button>
                  </div>
                </div>

                <table className="table w-full">
                  <thead>
                    <tr>
                      <th>Code</th>
                      <th>Subject</th>
                      <th>Credits</th>
                      <th>Grade</th>
                      <th>Points</th>
                      <th />
                    </tr>
                  </thead>

                  <tbody>
                    {s.subjects?.map((x) => (
                      <tr key={x.id}>
                        <td>{x.code}</td>
                        <td>{x.name}</td>
                        <td>{x.credits}</td>
                        <td>
                          <Select
                            value={x.grade_label}
                            onChange={(v) =>
                              run(
                                () =>
                                  send(
                                    "put",
                                    `/academics/semesters/${s.id}/subjects/${x.id}`,
                                    { grade_label: v }
                                  ),
                                "Grade updated"
                              )
                            }
                            options={(scale?.grades || []).map((g) => g.label)}
                          />
                        </td>
                        <td>
                          {x.counts_in_gpa ? x.grade_point : "excluded"}
                        </td>
                        <td>
                          <button
                            aria-label="Delete subject"
                            className="text-red-600"
                            onClick={() =>
                              run(
                                () =>
                                  send(
                                    "delete",
                                    `/academics/semesters/${s.id}/subjects/${x.id}`
                                  ),
                                "Subject deleted"
                              )
                            }
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>

                {scale && (
                  <div className="mt-3 grid gap-2 md:grid-cols-5">
                    <input
                      className="input"
                      placeholder="Code"
                      value={f.code}
                      onChange={(e) => setF("code", e.target.value)}
                    />

                    <input
                      className="input md:col-span-2"
                      placeholder="Subject name"
                      value={f.name}
                      onChange={(e) => setF("name", e.target.value)}
                    />

                    <input
                      className="input"
                      type="number"
                      min={0}
                      step="0.5"
                      placeholder="Credits"
                      value={f.credits}
                      onChange={(e) => setF("credits", e.target.value)}
                    />

                    <div className="flex gap-2">
                      <Select
                        value={f.grade_label}
                        placeholder="Grade"
                        options={scale.grades.map((g) => g.label)}
                        onChange={(v) => setF("grade_label", v)}
                      />

                      <button
                        className="btn-primary"
                        onClick={async () => {
                          if (
                            await run(
                              () =>
                                send(
                                  "post",
                                  `/academics/semesters/${s.id}/subjects`,
                                  clean({
                                    ...f,
                                    credits: Number(f.credits),
                                  })
                                ),
                              "Subject added"
                            )
                          ) {
                            setSub({
                              ...sub,
                              [s.id]: {
                                name: "",
                                code: "",
                                credits: "",
                                grade_label: "",
                              },
                            });
                          }
                        }}
                      >
                        Add
                      </button>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {semForm && (
        <Modal
          title={semForm.id ? "Edit semester" : "Add semester"}
          onClose={() => setSemForm(null)}
        >
          <div className="grid gap-3 md:grid-cols-2">
            <Field label="Number">
              <input
                className="input"
                type="number"
                min={1}
                max={20}
                value={semForm.number}
                onChange={(e) =>
                  setSemForm({ ...semForm, number: e.target.value })
                }
              />
            </Field>

            <Field label="Title (optional)">
              <input
                className="input"
                value={semForm.title}
                onChange={(e) =>
                  setSemForm({ ...semForm, title: e.target.value })
                }
              />
            </Field>

            <Field label="Academic year">
              <input
                className="input"
                placeholder="2025-26"
                value={semForm.academic_year}
                onChange={(e) =>
                  setSemForm({ ...semForm, academic_year: e.target.value })
                }
              />
            </Field>

            <Field label="Grading scale">
              <ScalePicker
                scales={scales}
                value={semForm.grading_scale_id}
                onChange={(v) =>
                  setSemForm({ ...semForm, grading_scale_id: v })
                }
              />
            </Field>
          </div>

          <p className="mt-2 text-xs text-slate-500">
            If you change the scale, existing grades are re-mapped, so their
            labels must exist in the new scale.
          </p>

          <button
            className="btn-primary mt-4"
            onClick={saveSem}
            disabled={!semForm.grading_scale_id}
          >
            Save
          </button>
        </Modal>
      )}
    </>
  );
}
