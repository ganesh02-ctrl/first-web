import { Download, Eye, FolderPlus, Trash2, Upload } from "lucide-react";
import { useState } from "react";
import { Badge, Empty, ErrorState, Field, Modal, PageHeader, Select, Spinner } from "../components/common/ui";
import { useToast } from "../contexts/ToastContext";
import { useApi } from "../hooks/useApi";
import { useVocab } from "../hooks/useVocab";
import { api, errorMessage, get, openFile, send } from "../services/api";
import type { Doc } from "../types";
import { bytes, date } from "../utils/format";

export default function Documents() {
  const vocab = useVocab(); const { notify } = useToast();
  const [folder, setFolder] = useState("");
  const folders = useApi(() => get<{ id: number; name: string; document_count: number }[]>("/documents/folders"));
  const { data, loading, error, reload } = useApi(() => get<Doc[]>("/documents", folder ? { folder_id: folder } : {}), [folder]);
  const checklist = useApi(() => get<any>("/documents/checklist"));
  const [up, setUp] = useState<any>(null);
  const refresh = () => { reload(); folders.reload(); checklist.reload(); };
  const run = async (fn: () => Promise<unknown>, ok: string) => { try { await fn(); notify(ok); refresh(); return true; } catch (e) { notify(errorMessage(e), "error"); return false; } };

  const upload = async () => {
    if (!up.file) return notify("Choose a file", "error");
    const fd = new FormData();
    Object.entries(up).forEach(([k, v]) => v !== "" && v != null && fd.append(k, v as any));
    if (await run(() => api.post("/documents", fd), "Uploaded")) setUp(null);
  };
  return (
    <>
      <PageHeader title="Document vault" subtitle="Your files are private. Every download needs you to be signed in." actions={<>
        <button className="btn-secondary" onClick={() => { const n = prompt("Folder name"); if (n) run(() => send("post", "/documents/folders", { name: n }), "Folder created"); }}><FolderPlus className="h-4 w-4" />Folder</button>
        <button className="btn-primary" onClick={() => setUp({ file: null, display_name: "", document_type: "other", folder_id: folder, issued_on: "", expires_on: "" })}><Upload className="h-4 w-4" />Upload</button></>} />
      <div className="grid gap-4 lg:grid-cols-4">
        <div className="card space-y-1 text-sm">
          <button className={`block w-full rounded px-2 py-1 text-left ${!folder ? "bg-royal-500/10" : ""}`} onClick={() => setFolder("")}>All documents</button>
          {folders.data?.map((fo) => <div key={fo.id} className={`flex items-center justify-between rounded px-2 py-1 ${folder === String(fo.id) ? "bg-royal-500/10" : ""}`}>
            <button onClick={() => setFolder(String(fo.id))}>{fo.name} ({fo.document_count})</button>
            <span className="space-x-2 text-xs"><button onClick={() => { const n = prompt("Rename folder", fo.name); if (n) run(() => send("patch", `/documents/folders/${fo.id}`, { name: n }), "Renamed"); }}>Rename</button>
              <button className="text-red-600" onClick={() => confirm("Delete folder? Documents are kept.") && run(() => send("delete", `/documents/folders/${fo.id}`), "Folder deleted")}>✕</button></span></div>)}
          <div className="mt-4 border-t pt-3"><h3 className="mb-1 font-semibold">Missing for tracked scholarships</h3>
            {checklist.data?.items?.length ? checklist.data.missing.length === 0 ? <p className="text-emerald-600">You have every listed document.</p> :
              <ul className="list-disc pl-4">{checklist.data.missing.map((m: any) => <li key={m.document_type}>{m.name}</li>)}</ul>
              : <p className="text-slate-500">Track scholarships to see which documents they need.</p>}</div>
        </div>
        <div className="lg:col-span-3">
          {loading ? <Spinner /> : error ? <ErrorState message={error} onRetry={reload} /> : data!.length === 0 ? <Empty title="No documents" /> :
            <div className="card overflow-x-auto"><table className="table w-full"><thead><tr><th>Name</th><th>Type</th><th>Size</th><th>Expires</th><th>Folder</th><th /></tr></thead>
              <tbody>{data!.map((d) => <tr key={d.id}><td>{d.display_name}</td><td>{d.document_type_label}</td><td>{bytes(d.size_bytes)}</td>
                <td>{d.expires_on ? <>{date(d.expires_on)} {d.is_expired ? <Badge value="expired" /> : d.days_to_expiry! <= 30 && <Badge value="needs_review" text={`${d.days_to_expiry}d`} />}</> : "—"}</td>
                <td><Select value={d.folder_id ?? ""} placeholder="None" options={(folders.data || []).map((f) => ({ value: f.id, label: f.name }))}
                  onChange={(v) => run(() => send("patch", `/documents/${d.id}`, { folder_id: v ? Number(v) : null }), "Moved")} /></td>
                <td className="flex gap-2">{d.previewable && <button aria-label="Preview" onClick={() => openFile(`/documents/${d.id}/preview`)}><Eye className="h-4 w-4" /></button>}
                  <button aria-label="Download" onClick={() => openFile(`/documents/${d.id}/download`, d.original_filename)}><Download className="h-4 w-4" /></button>
                  <button aria-label="Delete" className="text-red-600" onClick={() => confirm("Delete this document?") && run(() => send("delete", `/documents/${d.id}`), "Deleted")}><Trash2 className="h-4 w-4" /></button></td></tr>)}</tbody></table></div>}
        </div>
      </div>
      {up && <Modal title="Upload document" onClose={() => setUp(null)}>
        <div className="grid gap-3 md:grid-cols-2">
          <div className="md:col-span-2"><Field label="File (PDF, PNG, JPG, WEBP — max 10 MB)"><input className="input" type="file" accept=".pdf,.png,.jpg,.jpeg,.webp" onChange={(e) => setUp({ ...up, file: e.target.files?.[0] })} /></Field></div>
          <Field label="Display name"><input className="input" value={up.display_name} onChange={(e) => setUp({ ...up, display_name: e.target.value })} /></Field>
          <Field label="Type"><Select value={up.document_type} onChange={(v) => setUp({ ...up, document_type: v })} options={Object.entries(vocab?.document_types || {}).map(([value, label]) => ({ value, label }))} /></Field>
          <Field label="Folder"><Select value={up.folder_id} onChange={(v) => setUp({ ...up, folder_id: v })} placeholder="None" options={(folders.data || []).map((f) => ({ value: f.id, label: f.name }))} /></Field>
          <Field label="Issued on"><input className="input" type="date" value={up.issued_on} onChange={(e) => setUp({ ...up, issued_on: e.target.value })} /></Field>
          <Field label="Expires on"><input className="input" type="date" value={up.expires_on} onChange={(e) => setUp({ ...up, expires_on: e.target.value })} /></Field>
        </div>
        <button className="btn-primary mt-4" onClick={upload}>Upload</button>
      </Modal>}
    </>
  );
}
