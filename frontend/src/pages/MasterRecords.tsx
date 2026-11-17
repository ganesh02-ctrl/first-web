import {
  FormEvent,
  useEffect,
  useRef,
  useState,
} from "react";
import {
  Download,
  FileText,
  Pencil,
  Plus,
  RefreshCw,
  Trash2,
} from "lucide-react";
import {
  ErrorState,
  Spinner,
} from "../components/common/ui";
import { useToast } from "../contexts/ToastContext";
import {
  api,
  errorMessage,
  openFile,
  send,
} from "../services/api";
import {
  MasterData,
  preview,
  score,
  SubjectRecord,
  Summary,
} from "../services/master";
import "./master.css";

const ROOT = "/master-semesters";

type Draft = {
  name: string;
  code: string;
  maximum_marks: string;
  passing_marks: string;
  marks_obtained: string;
  credits: string;
};

const empty: Draft = {
  name: "",
  code: "",
  maximum_marks: "",
  passing_marks: "",
  marks_obtained: "",
  credits: "",
};

const fields: [keyof Draft, string][] = [
  ["name", "Subject name"],
  ["code", "Course code"],
  ["maximum_marks", "Maximum marks"],
  ["passing_marks", "Minimum passing marks"],
  ["marks_obtained", "Marks obtained"],
  ["credits", "Credits"],
];

function Metrics({
  info,
  title,
}: {
  info: Summary;
  title: string;
}) {
  return (
    <div className="ms-metrics" aria-label={title}>
      <div>
        <span>{title}</span>
        <strong>{score(info.gpa)}</strong>
        <small>Grade {info.grade || "—"}</small>
      </div>

      <div>
        <span>GPA credits</span>
        <strong>{score(info.total_credits)}</strong>
        <small>
          Passed: {score(info.completed_credits)}
        </small>
      </div>

      <div>
        <span>Raw marks percentage</span>
        <strong>
          {score(info.raw_percentage)}
          {info.raw_percentage != null && "%"}
        </strong>
      </div>

      <div>
        <span>Institutional conversion</span>
        <strong>
          {score(info.converted_percentage)}
          {info.converted_percentage != null && "%"}
        </strong>
      </div>
    </div>
  );
}

export default function MasterRecords() {
  const [data, setData] = useState<MasterData | null>(
    null,
  );
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [refresh, setRefresh] = useState(0);
  const [expanded, setExpanded] = useState<
    Set<number>
  >(() => new Set());

  const [editor, setEditor] = useState<{
    semester: number;
    subject?: SubjectRecord;
  } | null>(null);

  const [draft, setDraft] = useState<Draft>(empty);
  const formRef = useRef<HTMLFormElement>(null);
  const active = useRef(true);
  const { notify } = useToast();

  useEffect(() => {
    active.current = true;
    return () => {
      active.current = false;
    };
  }, []);

  useEffect(() => {
    const abort = new AbortController();
    setLoading(true);
    setError("");

    api
      .get(ROOT, { signal: abort.signal })
      .then((response) => setData(response.data.data))
      .catch((err) => {
        if (!abort.signal.aborted) {
          setError(errorMessage(err));
        }
      })
      .finally(() => {
        if (!abort.signal.aborted) {
          setLoading(false);
        }
      });

    return () => abort.abort();
  }, [refresh]);

  useEffect(() => {
    if (editor) {
      formRef.current
        ?.querySelector<HTMLInputElement>("input")
        ?.focus();
    }
  }, [editor]);

  function edit(
    semester: number,
    subject?: SubjectRecord,
  ) {
    if (
      editor &&
      !window.confirm(
        "Discard the current unsaved subject form?",
      )
    ) {
      return;
    }

    setDraft(
      subject
        ? (Object.fromEntries(
            fields.map(([key]) => [
              key,
              subject[key] == null
                ? ""
                : String(subject[key]),
            ]),
          ) as Draft)
        : { ...empty },
    );

    setEditor({ semester, subject });
  }

  async function save(event: FormEvent) {
    event.preventDefault();
    if (!editor || busy) return;

    const marks = [
      draft.maximum_marks,
      draft.passing_marks,
      draft.marks_obtained,
    ];

    if (
      marks.some(
        (value) =>
          value !== "" &&
          (!Number.isFinite(Number(value)) ||
            Number(value) < 0),
      ) ||
      (draft.maximum_marks !== "" &&
        (Number(draft.maximum_marks) <= 0 ||
          marks
            .slice(1)
            .some(
              (value) =>
                value !== "" &&
                Number(value) >
                  Number(draft.maximum_marks),
            )))
    ) {
      notify(
        "Check maximum, passing and obtained marks",
        "error",
      );
      return;
    }

    const body = {
      name: draft.name.trim(),
      code: draft.code.trim(),
      credits: Number(draft.credits),
      maximum_marks:
        draft.maximum_marks === ""
          ? null
          : Number(draft.maximum_marks),
      passing_marks:
        draft.passing_marks === ""
          ? null
          : Number(draft.passing_marks),
      marks_obtained:
        draft.marks_obtained === ""
          ? null
          : Number(draft.marks_obtained),
      ...(editor.subject
        ? { version: editor.subject.version }
        : {}),
    };

    setBusy(true);

    try {
      const identifier = editor.subject?.id;
      const result = await send<MasterData>(
        identifier ? "put" : "post",
        `${ROOT}/${editor.semester}/subjects${
          identifier ? `/${identifier}` : ""
        }`,
        body,
      );

      if (active.current) {
        setData(result);
        setEditor(null);
        notify(
          "Subject saved; all cumulative results recalculated",
        );
      }
    } catch (err) {
      if (active.current) {
        notify(errorMessage(err), "error");
      }
    } finally {
      if (active.current) setBusy(false);
    }
  }

  async function remove(
    semester: number,
    subject: SubjectRecord,
  ) {
    if (
      !window.confirm(
        `Permanently delete ${subject.name}?`,
      )
    ) {
      return;
    }

    setBusy(true);

    try {
      const result = await send<MasterData>(
        "delete",
        `${ROOT}/${semester}/subjects/${subject.id}`,
        { version: subject.version },
      );

      if (active.current) {
        setData(result);
        notify(
          "Subject deleted; results recalculated",
        );
      }
    } catch (err) {
      if (active.current) {
        notify(errorMessage(err), "error");
      }
    } finally {
      if (active.current) setBusy(false);
    }
  }

  async function report(kind: "pdf" | "xlsx") {
    setBusy(true);
    try {
      await openFile(
        `${ROOT}/report.${kind}`,
        `master-semester-report.${kind}`,
      );
    } catch (err) {
      if (active.current) {
        notify(errorMessage(err), "error");
      }
    } finally {
      if (active.current) setBusy(false);
    }
  }

  if (loading) return <Spinner />;

  if (error || !data) {
    return (
      <ErrorState
        message={error || "Unable to load records"}
        onRetry={() => setRefresh((value) => value + 1)}
      />
    );
  }

  return (
    <section
      className="master"
      aria-label="Master semester records"
    >
      <header className="ms-header">
        <div>
          <p className="ms-eyebrow">
            SSS · ACADEMIC PERFORMANCE
          </p>
          <h1>MASTER SEMESTER RECORDS</h1>
          <p>
            {data.student.name} · Eight semesters.
            One academic record.
          </p>
        </div>

        <div className="ms-actions">
          <button
            disabled={busy || !!editor}
            onClick={() =>
              setRefresh((value) => value + 1)
            }
            aria-label="Refresh saved records"
          >
            <RefreshCw size={16} />
          </button>

          <button
            disabled={busy || !!editor}
            onClick={() => report("xlsx")}
          >
            <Download size={16} />
            Excel
          </button>

          <button
            className="ms-primary"
            disabled={busy || !!editor}
            onClick={() => report("pdf")}
          >
            <FileText size={16} />
            GENERATE MASTER SEMESTER REPORT
          </button>
        </div>
      </header>

      <aside className="ms-notice">
        <b>{data.policy.configuration.name}</b>
        {" · "}Policy version {data.policy.version}.
        {" "}
        {data.policy.configuration.include_failed
          ? "Failed subjects remain in GPA credits."
          : "Failed subjects are excluded from GPA credits."}
        <p>
          Draft, historical and invalid subjects are
          excluded. Summaries are provisional when
          records are missing. Historical grades are
          preserved; enter actual marks to include
          them. PDF reports can be printed from your
          PDF viewer.
        </p>
      </aside>

      <nav
        className="ms-sem-nav"
        aria-label="Jump to semester"
      >
        {data.semesters.map((semester) => (
          <a
            key={semester.number}
            href={`#semester-${semester.number}`}
            onClick={() =>
              setExpanded((value) =>
                new Set(value).add(semester.number),
              )
            }
          >
            Semester {semester.number}
          </a>
        ))}
      </nav>

      {data.semesters.map((semester) => (
        <details
          id={`semester-${semester.number}`}
          className="ms-semester"
          key={semester.number}
          open={expanded.has(semester.number)}
          onToggle={(event) => {
            const open = event.currentTarget.open;
            setExpanded((value) => {
              if (
                value.has(semester.number) === open
              ) {
                return value;
              }
              const next = new Set(value);
              if (open) {
                next.add(semester.number);
              } else {
                next.delete(semester.number);
              }
              return next;
            });
          }}
        >
          <summary>
            <span>
              <b>Semester {semester.number}</b>
              <small>
                {semester.subjects.length} subjects
                {" · "}
                {semester.completed
                  ? "Completed"
                  : semester.subjects.length
                    ? "In progress"
                    : "No records"}
                {semester.academic_year &&
                  ` · ${semester.academic_year}`}
              </small>
            </span>

            <span className="ms-sem-score">
              SGPA <b>{score(semester.sgpa)}</b>
              <small>
                Cumulative{" "}
                {score(semester.cumulative.gpa)}
              </small>
            </span>
          </summary>

          <div className="ms-content">
            <div className="ms-actions">
              <button
                className="ms-primary"
                disabled={busy}
                onClick={() =>
                  edit(semester.number)
                }
              >
                <Plus size={16} />
                Add Subject
              </button>
            </div>

            <div
              className="ms-table-wrap"
              tabIndex={0}
              role="region"
              aria-label={`Semester ${semester.number} subject table`}
            >
              <table>
                <caption>
                  Saved subjects — Semester{" "}
                  {semester.number}
                </caption>

                <thead>
                  <tr>
                    {[
                      "Subject name",
                      "Course code",
                      "Maximum",
                      "Passing",
                      "Obtained",
                      "Credits",
                      "Grade",
                      "Point",
                      "Result",
                      "Actions",
                    ].map((heading) => (
                      <th
                        key={heading}
                        scope="col"
                      >
                        {heading}
                      </th>
                    ))}
                  </tr>
                </thead>

                <tbody>
                  {semester.subjects.map(
                    (subject) => (
                      <tr key={subject.id}>
                        <th scope="row">
                          {subject.name}
                        </th>
                        <td>
                          {subject.code || "—"}
                        </td>
                        <td>
                          {score(
                            subject.maximum_marks,
                          )}
                        </td>
                        <td>
                          {score(
                            subject.passing_marks,
                          )}
                        </td>
                        <td>
                          {score(
                            subject.marks_obtained,
                          )}
                        </td>
                        <td>
                          {score(subject.credits)}
                        </td>
                        <td>
                          {subject.grade ||
                            (subject.legacy_grade
                              ? `${subject.legacy_grade} (historical)`
                              : "—")}
                        </td>
                        <td>
                          {score(
                            subject.grade_point,
                          )}
                        </td>
                        <td>
                          <span
                            className={`ms-status ${
                              subject.result ===
                              "Fail"
                                ? "ms-fail"
                                : ""
                            }`}
                          >
                            {subject.result}
                          </span>
                        </td>
                        <td>
                          <div className="ms-actions">
                            <button
                              disabled={busy}
                              aria-label={`Edit ${subject.name}`}
                              onClick={() =>
                                edit(
                                  semester.number,
                                  subject,
                                )
                              }
                            >
                              <Pencil size={15} />
                            </button>
                            <button
                              disabled={
                                busy || !!editor
                              }
                              aria-label={`Delete ${subject.name}`}
                              onClick={() =>
                                remove(
                                  semester.number,
                                  subject,
                                )
                              }
                            >
                              <Trash2 size={15} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ),
                  )}

                  {!semester.subjects.length && (
                    <tr>
                      <td
                        colSpan={10}
                        className="ms-empty"
                      >
                        No subjects yet. Add your
                        first subject to begin.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {editor?.semester ===
              semester.number && (
              <form
                ref={formRef}
                className="ms-editor"
                onSubmit={save}
                aria-label="Subject editor"
              >
                <h3>
                  {editor.subject
                    ? "Edit subject"
                    : "Add subject"}
                </h3>

                <div className="ms-fields">
                  {fields.map(([key, label]) => (
                    <label key={key}>
                      {label}
                      <input
                        name={key}
                        value={draft[key]}
                        disabled={busy}
                        type={
                          key === "name" ||
                          key === "code"
                            ? "text"
                            : "number"
                        }
                        required={
                          key === "name" ||
                          key === "credits"
                        }
                        maxLength={
                          key === "name"
                            ? 200
                            : key === "code"
                              ? 30
                              : undefined
                        }
                        min={
                          key === "credits" ||
                          key === "maximum_marks"
                            ? "0.01"
                            : "0"
                        }
                        step="0.01"
                        max={
                          key === "credits"
                            ? "999.99"
                            : key === "name" ||
                                key === "code"
                              ? undefined
                              : "99999999.99"
                        }
                        onChange={(event) =>
                          setDraft((value) => ({
                            ...value,
                            [key]:
                              event.target.value,
                          }))
                        }
                      />
                    </label>
                  ))}
                </div>

                <p role="status">
                  {preview(
                    draft.maximum_marks,
                    draft.passing_marks,
                    draft.marks_obtained,
                    data.policy.configuration,
                  )}
                </p>

                <p className="ms-help">
                  Blank marks save an incomplete
                  record, not a zero. Save to update
                  all official summaries.
                </p>

                <div className="ms-actions">
                  <button
                    className="ms-primary"
                    disabled={busy}
                  >
                    {busy
                      ? "Saving…"
                      : "Save subject"}
                  </button>
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() =>
                      setEditor(null)
                    }
                  >
                    Cancel
                  </button>
                </div>
              </form>
            )}

            <Metrics
              info={semester}
              title="Semester SGPA"
            />

            <div className="ms-cumulative">
              Cumulative CGPA (Semesters 1–
              {semester.number}):{" "}
              <b>
                {score(semester.cumulative.gpa)}
              </b>
              {" · "}Grade{" "}
              {semester.cumulative.grade || "—"}
              {" · "}Passed credits{" "}
              {score(
                semester.cumulative.completed_credits,
              )}
            </div>

            {(semester.pending_subjects > 0 ||
              semester.failed_subjects > 0) && (
              <p className="ms-help">
                {semester.pending_subjects}{" "}
                pending/historical subjects ·{" "}
                {semester.failed_subjects} failed
                subjects. Results use only eligible
                saved records.
              </p>
            )}
          </div>
        </details>
      ))}

      <section
        className="ms-total"
        aria-label="Total CGPA"
      >
        <p className="ms-eyebrow">
          CREDIT-WEIGHTED · ALL EIGHT SEMESTERS
        </p>
        <h2>TOTAL CGPA</h2>

        <Metrics
          info={data.total}
          title="Total CGPA"
        />

        <p>
          {data.total.completed_semesters} / 8
          completed semesters ·{" "}
          {data.total.pending_subjects}{" "}
          pending/historical subjects ·{" "}
          {data.total.failed_subjects} failed
          subjects
        </p>

        <p className="ms-help">
          Raw percentage = total valid marks
          obtained ÷ total valid maximum marks ×
          100. Institutional conversion:{" "}
          {data.policy.configuration.conversion ||
            "Not configured"}
          . An empty semester is never counted as
          completed.
        </p>
      </section>
    </section>
  );
}
