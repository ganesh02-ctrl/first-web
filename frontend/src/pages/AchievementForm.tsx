import { FormEvent, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Field, PageHeader, Select } from "../components/common/ui";
import { useToast } from "../contexts/ToastContext";
import { useApi } from "../hooks/useApi";
import { useVocab } from "../hooks/useVocab";
import { api, errorMessage, get, send } from "../services/api";
import type { Achievement, Doc } from "../types";
import { clean } from "../utils/format";

const empty = { title: "", description: "", organization: "", category: "academic", achieved_on: "", rank_position: "",
  location_name: "", latitude: "", longitude: "", certificate_document_id: "", is_public: false };

export default function AchievementForm() {
  const { id } = useParams(); const nav = useNavigate(); const vocab = useVocab(); const { notify } = useToast();
  const docs = useApi(() => get<Doc[]>("/documents")).data || [];
  const [f, setF] = useState<any>(empty); const [file, setFile] = useState<File | null>(null); const [busy, setBusy] = useState(false);
  useEffect(() => { if (id) get<Achievement>(`/achievements/${id}`).then((a) =>
    setF({ ...empty, ...Object.fromEntries(Object.entries(a).map(([k, v]) => [k, v ?? ""])) })); }, [id]);
  const set = (k: string) => (e: any) => setF({ ...f, [k]: e.target.value });

  const submit = async (e: FormEvent) => {
    e.preventDefault(); setBusy(true);
    try {
      let certId = f.certificate_document_id;
      if (file) {
        const fd = new FormData(); fd.append("file", file); fd.append("display_name", `Certificate — ${f.title}`); fd.append("document_type", "other");
        certId = (await api.post("/documents", fd)).data.data.id;
      }
      const body: any = clean({ title: f.title, description: f.description, organization: f.organization, category: f.category,
        achieved_on: f.achieved_on, rank_position: f.rank_position, location_name: f.location_name, is_public: f.is_public });
      body.latitude = f.latitude === "" ? null : Number(f.latitude); body.longitude = f.longitude === "" ? null : Number(f.longitude);
      body.certificate_document_id = certId === "" ? null : Number(certId);
      await (id ? send("put", `/achievements/${id}`, body) : send("post", "/achievements", body));
      notify("Achievement saved"); nav("/achievements");
    } catch (x) { notify(errorMessage(x), "error"); } finally { setBusy(false); }
  };
  return (
    <>
      <PageHeader title={id ? "Edit achievement" : "Add achievement"} />
      <form onSubmit={submit} className="card grid max-w-3xl gap-3 md:grid-cols-2">
        <Field label="Title"><input className="input" required value={f.title} onChange={set("title")} /></Field>
        <Field label="Category"><Select value={f.category} onChange={(v) => setF({ ...f, category: v })} options={vocab?.achievement_categories || []} /></Field>
        <Field label="Organization"><input className="input" value={f.organization} onChange={set("organization")} /></Field>
        <Field label="Date"><input className="input" type="date" required value={f.achieved_on} onChange={set("achieved_on")} /></Field>
        <Field label="Rank / position"><input className="input" value={f.rank_position} onChange={set("rank_position")} /></Field>
        <Field label="Location name"><input className="input" value={f.location_name} onChange={set("location_name")} /></Field>
        <Field label="Latitude (optional)"><input className="input" type="number" step="any" value={f.latitude} onChange={set("latitude")} /></Field>
        <Field label="Longitude (optional)"><input className="input" type="number" step="any" value={f.longitude} onChange={set("longitude")} /></Field>
        <div className="md:col-span-2"><Field label="Description"><textarea className="input" rows={3} value={f.description} onChange={set("description")} /></Field></div>
        <Field label="Certificate from vault"><Select value={f.certificate_document_id} onChange={(v) => setF({ ...f, certificate_document_id: v })} placeholder="None" options={docs.map((d) => ({ value: d.id, label: d.display_name }))} /></Field>
        <Field label="…or upload new (PDF/PNG/JPG/WEBP)"><input className="input" type="file" accept=".pdf,.png,.jpg,.jpeg,.webp" onChange={(e) => setFile(e.target.files?.[0] || null)} /></Field>
        <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={!!f.is_public} onChange={(e) => setF({ ...f, is_public: e.target.checked })} />Show on public portfolio</label>
        <div className="flex justify-end gap-2 md:col-span-2"><button type="button" className="btn-secondary" onClick={() => nav(-1)}>Cancel</button>
          <button className="btn-primary" disabled={busy}>{busy ? "Saving…" : "Save"}</button></div>
      </form>
    </>
  );
}
