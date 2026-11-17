import {
  FormEvent,
  useEffect,
  useState,
} from "react";
import {
  ErrorState,
  Spinner,
} from "../../components/common/ui";
import { useToast } from "../../contexts/ToastContext";
import {
  api,
  errorMessage,
  send,
} from "../../services/api";
import {
  Band,
  Policy,
  PolicyConfig,
} from "../../services/master";
import "../master.css";

export default function GradingPolicy() {
  const [policy, setPolicy] =
    useState<Policy | null>(null);
  const [error, setError] = useState("");
  const [reload, setReload] = useState(0);
  const [busy, setBusy] = useState(false);
  const { notify } = useToast();

  useEffect(() => {
    const abort = new AbortController();
    setError("");

    api
      .get("/master-semesters/policy", {
        signal: abort.signal,
      })
      .then((response) =>
        setPolicy(response.data.data),
      )
      .catch((err) => {
        if (!abort.signal.aborted) {
          setError(errorMessage(err));
        }
      });

    return () => abort.abort();
  }, [reload]);

  function patch<K extends keyof PolicyConfig>(
    key: K,
    value: PolicyConfig[K],
  ) {
    setPolicy(
      (current) =>
        current && {
          ...current,
          configuration: {
            ...current.configuration,
            [key]: value,
          },
        },
    );
  }

  function band(
    index: number,
    key: keyof Band,
    value: string | number | boolean,
  ) {
    if (!policy) return;

    patch(
      "bands",
      policy.configuration.bands.map(
        (current, position) =>
          position === index
            ? { ...current, [key]: value }
            : current,
      ),
    );
  }

  async function save(event: FormEvent) {
    event.preventDefault();

    if (
      !window.confirm(
        "Apply this policy to all marks-based records? " +
          "Historical grade-only records remain unchanged.",
      )
    ) {
      return;
    }

    setBusy(true);

    try {
      setPolicy(
        await send<Policy>(
          "put",
          "/master-semesters/policy",
          policy,
        ),
      );
      notify(
        "Policy saved. All master records and reports use the new version.",
      );
    } catch (err) {
      notify(errorMessage(err), "error");
    } finally {
      setBusy(false);
    }
  }

  if (error) {
    return (
      <ErrorState
        message={error}
        onRetry={() =>
          setReload((value) => value + 1)
        }
      />
    );
  }

  if (!policy) return <Spinner />;

  const configuration = policy.configuration;

  return (
    <section className="master">
      <header className="ms-header">
        <div>
          <p className="ms-eyebrow">
            ADMINISTRATION · ACADEMIC SETTINGS
          </p>
          <h1>Grading Policy</h1>
          <p>
            Institution-wide policy · version{" "}
            {policy.version}
          </p>
        </div>
      </header>

      <div className="ms-notice">
        Review against your institution&apos;s
        regulations before saving. Existing marks
        are re-evaluated on every fetch and report.
        Historical grades without marks are never
        invented or overwritten.
        <p>
          Boundaries are minimum-inclusive and
          maximum-exclusive; the highest maximum is
          inclusive. Use one lowest failing band,
          ascending grade points and no gaps.
          Aggregate grade uses grade-point
          thresholds. For absolute marks policies,
          configure a boundary range covering the
          subjects&apos; maximum marks.
        </p>
      </div>

      <form
        className="ms-editor"
        onSubmit={save}
      >
        <fieldset disabled={busy}>
          <legend>Policy configuration</legend>

          <div className="ms-fields">
            <label>
              Policy name
              <input
                required
                maxLength={150}
                value={configuration.name}
                onChange={(event) =>
                  patch(
                    "name",
                    event.target.value,
                  )
                }
              />
            </label>

            <label>
              Boundary basis
              <select
                value={configuration.basis}
                onChange={(event) =>
                  patch(
                    "basis",
                    event.target
                      .value as PolicyConfig["basis"],
                  )
                }
              >
                <option value="percentage">
                  Percentage
                </option>
                <option value="marks">
                  Absolute marks
                </option>
              </select>
            </label>

            <label>
              Boundary maximum
              <input
                required
                type="number"
                step="0.01"
                min="0.01"
                value={
                  configuration.boundary_max
                }
                onChange={(event) =>
                  patch(
                    "boundary_max",
                    Number(event.target.value),
                  )
                }
              />
            </label>

            <label>
              Maximum grade point
              <input
                required
                type="number"
                step="0.01"
                min="0.01"
                max="99.99"
                value={configuration.max_point}
                onChange={(event) =>
                  patch(
                    "max_point",
                    Number(event.target.value),
                  )
                }
              />
            </label>

            <label>
              CGPA-to-percentage formula
              <input
                maxLength={120}
                value={
                  configuration.conversion
                }
                onChange={(event) =>
                  patch(
                    "conversion",
                    event.target.value,
                  )
                }
              />
            </label>
          </div>

          <p className="ms-help">
            Leave conversion blank if not
            prescribed. Variables: gpa, max_point.
            Supported: + − * / and parentheses.
            Linear expressions only, e.g. (gpa -
            0.75) * 10. The result is displayed
            separately from raw percentage,
            without silently clamping it.
          </p>

          <label className="ms-check">
            <input
              type="checkbox"
              checked={
                configuration.include_failed
              }
              onChange={(event) =>
                patch(
                  "include_failed",
                  event.target.checked,
                )
              }
            />
            Include failed subjects in GPA credits
          </label>

          <div className="ms-table-wrap">
            <table>
              <caption>Grade boundaries</caption>
              <thead>
                <tr>
                  <th>Grade</th>
                  <th>Minimum</th>
                  <th>Maximum</th>
                  <th>Grade point</th>
                  <th>Passing</th>
                  <th>Action</th>
                </tr>
              </thead>

              <tbody>
                {configuration.bands.map(
                  (current, index) => (
                    <tr key={index}>
                      <td>
                        <input
                          aria-label={`Grade ${
                            index + 1
                          }`}
                          required
                          maxLength={10}
                          value={current.letter}
                          onChange={(event) =>
                            band(
                              index,
                              "letter",
                              event.target.value,
                            )
                          }
                        />
                      </td>

                      {(
                        [
                          "min",
                          "max",
                          "point",
                        ] as const
                      ).map((key) => (
                        <td key={key}>
                          <input
                            aria-label={`${key} band ${
                              index + 1
                            }`}
                            required
                            type="number"
                            step="0.01"
                            min="0"
                            value={current[key]}
                            onChange={(event) =>
                              band(
                                index,
                                key,
                                Number(
                                  event.target.value,
                                ),
                              )
                            }
                          />
                        </td>
                      ))}

                      <td>
                        <input
                          aria-label={`Passing band ${
                            index + 1
                          }`}
                          type="checkbox"
                          checked={
                            current.passing
                          }
                          onChange={(event) =>
                            band(
                              index,
                              "passing",
                              event.target.checked,
                            )
                          }
                        />
                      </td>

                      <td>
                        <button
                          type="button"
                          disabled={
                            configuration.bands
                              .length <= 2
                          }
                          onClick={() =>
                            patch(
                              "bands",
                              configuration.bands.filter(
                                (
                                  _,
                                  position,
                                ) =>
                                  position !==
                                  index,
                              ),
                            )
                          }
                        >
                          Remove
                        </button>
                      </td>
                    </tr>
                  ),
                )}
              </tbody>
            </table>
          </div>

          <div className="ms-actions">
            <button
              type="button"
              disabled={
                configuration.bands.length >=
                30
              }
              onClick={() =>
                patch("bands", [
                  ...configuration.bands,
                  {
                    letter: "",
                    min:
                      configuration.boundary_max,
                    max:
                      configuration.boundary_max,
                    point:
                      configuration.max_point,
                    passing: true,
                  },
                ])
              }
            >
              Add grade band
            </button>

            <button className="ms-primary">
              {busy
                ? "Saving…"
                : "Save institutional policy"}
            </button>

            <button
              type="button"
              onClick={() => {
                setPolicy(null);
                setReload(
                  (value) => value + 1,
                );
              }}
            >
              Reload saved policy
            </button>
          </div>
        </fieldset>
      </form>
    </section>
  );
}
