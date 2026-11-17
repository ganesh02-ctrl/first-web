
import { Plus, Upload, Send } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { Badge, Empty, ErrorState, Field, Modal, PageHeader, Pager, Select, Spinner } from "../../components/common/ui";
import { useToast } from "../../contexts/ToastContext";
import { useApi } from "../../hooks/useApi";
import { api, errorMessage, getPage, send } from "../../services/api";
import type { ScholarshipSummary } from "../../types";
import { date } from "../../utils/format";

export default function AdminScholarships() {
  const { notify } = useToast();
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [publishing, setPublishing] = useState(false);

  const { data, loading, error, reload } = useApi(
    () => getPage<ScholarshipSummary>(
      "/admin/scholarships",
      { q: q || undefined, status: status || undefined, page }
    ),
    [q, status, page]
  );

  const [imp, setImp] = useState<{ file: File | null; result: any } | null>(null);

  const doImport = async (dry: boolean) => {
    if (!imp?.file) return;

    const fd = new FormData();
    fd.append("file", imp.file);
    fd.append("dry_run", String(dry));

    try {
      const r = await api.post("/admin/scholarships/import", fd);
      setImp({ ...imp, result: r.data.data });
      if (!dry) reload();
    } catch (e) {
      notify(errorMessage(e), "error");
    }
  };

  const del = async (s: ScholarshipSummary) => {
    if (!confirm(`Delete "${s.title}"?`)) return;

    try {
      await send("delete", `/admin/scholarships/${s.id}`);
      notify("Scholarship deleted successfully", "success");
      reload();
    } catch (e) {
      notify(errorMessage(e), "error");
    }
  };

  const publishAll = async () => {
    if (!confirm(
      "Publish all eligible verified scholarships? Unverified scholarships will not be published."
    )) return;

    setPublishing(true);

    try {
      const result = await send<any>(
        "post",
        "/admin/scholarships/publish-eligible"
      );

      const published = result?.data?.published_count ?? 0;
      const skipped = result?.data?.skipped_count ?? 0;

      notify(
        `Bulk publishing completed. Published: ${published}, Skipped: ${skipped}.`,
        "success"
      );

      reload();
    } catch (e) {
      notify(errorMessage(e), "error");
    } finally {
      setPublishing(false);
    }
  };

  return (
    <>
      <PageHeader
        title="Scholarship management"
        subtitle="Records start out unverified. Check each one against its official source, verify it, then publish."
        actions={
          <>
            <button
              className="btn-secondary"
              onClick={publishAll}
              disabled={publishing}
            >
              <Send className="h-4 w-4" />
              {publishing ? "Publishing..." : "Publish All Verified"}
            </button>

            <button
              className="btn-secondary"
              onClick={() => setImp({ file: null, result: null })}
            >
              <Upload className="h-4 w-4" />
              Import CSV
            </button>

            <Link
              className="btn-primary"
              to="/admin/scholarships/new"
            >
              <Plus className="h-4 w-4" />
              Add
            </Link>
          </>
        }
      />

      <div className="mb-4 flex gap-2">
        <input
          className="input"
          placeholder="Search"
          value={q}
          onChange={(e) => {
            setPage(1);
            setQ(e.target.value);
          }}
        />

        <div className="w-48">
          <Select
            value={status}
            onChange={(v) => {
              setPage(1);
              setStatus(v);
            }}
            options={["unverified", "verified", "needs_review", "expired"]}
            placeholder="Any status"
          />
        </div>
      </div>

      {loading ? (
        <Spinner />
      ) : error ? (
        <ErrorState message={error} onRetry={reload} />
      ) : data!.items.length === 0 ? (
        <Empty
          title="No records"
          text="Add records by hand, or import a CSV built from official sources."
        />
      ) : (
        <>
          <div className="card overflow-x-auto">
            <table className="table w-full">
              <thead>
                <tr>
                  <th>Title</th>
                  <th>Provider</th>
                  <th>Closes</th>
                  <th>Status</th>
                  <th>Published</th>
                  <th />
                </tr>
              </thead>

              <tbody>
                {data!.items.map((s) => (
                  <tr key={s.id}>
                    <td>{s.title}</td>
                    <td>{s.provider_name}</td>
                    <td>{date(s.application_close_date)}</td>
                    <td><Badge value={s.effective_status} /></td>
                    <td>{s.is_published ? "Yes" : "No"}</td>
                    <td className="space-x-3 text-sm">
                      <Link
                        className="text-royal-600"
                        to={`/admin/scholarships/${s.id}`}
                      >
                        Edit
                      </Link>

                      <button
                        className="text-red-600"
                        onClick={() => del(s)}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <Pager
            page={data!.meta.page}
            pages={data!.meta.pages}
            onPage={setPage}
          />
        </>
      )}

      {imp && (
        <Modal
          title="Import scholarships (CSV)"
          onClose={() => setImp(null)}
        >
          <p className="mb-2 text-xs text-slate-500">
            Required columns: title, provider_name, provider_type,
            scholarship_type, official_source_name, source_url,
            application_url. See docs/DATA_SOURCING_POLICY.md.
            Imported rows are always unverified and unpublished.
          </p>

          <Field label="CSV file">
            <input
              className="input"
              type="file"
              accept=".csv"
              onChange={(e) =>
                setImp({
                  file: e.target.files?.[0] || null,
                  result: null
                })
              }
            />
          </Field>

          <div className="mt-3 flex gap-2">
            <button
              className="btn-secondary"
              onClick={() => doImport(true)}
            >
              Dry run
            </button>

            <button
              className="btn-primary"
              onClick={() => doImport(false)}
            >
              Import
            </button>
          </div>

          {imp.result && (
            <pre className="mt-3 max-h-64 overflow-auto rounded bg-slate-100 p-2 text-xs dark:bg-slate-800">
              {JSON.stringify(imp.result, null, 2)}
            </pre>
          )}
        </Modal>
      )}
    </>
  );
}
