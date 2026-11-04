import { Download, Plus, Share2 } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import AchievementCard from "../components/achievement/AchievementCard";
import { Empty, ErrorState, PageHeader, Select, Spinner } from "../components/common/ui";
import { useToast } from "../contexts/ToastContext";
import { useApi } from "../hooks/useApi";
import { useVocab } from "../hooks/useVocab";
import { errorMessage, get, openFile, send } from "../services/api";
import type { Achievement } from "../types";

export default function Achievements() {
  const vocab = useVocab(); const { notify } = useToast(); const [cat, setCat] = useState("");
  const { data, loading, error, reload } = useApi(() => get<Achievement[]>("/achievements", cat ? { category: cat } : {}), [cat]);
  const profile = useApi(() => get<any>("/students/me/profile"));
  const togglePortfolio = async () => {
    try { await send("patch", "/students/me/profile", { public_portfolio_enabled: !profile.data?.public_portfolio_enabled }); profile.reload(); notify("Portfolio setting saved"); }
    catch (e) { notify(errorMessage(e), "error"); }
  };
  const del = async (id: number) => { if (!confirm("Delete this achievement?")) return;
    try { await send("delete", `/achievements/${id}`); reload(); } catch (e) { notify(errorMessage(e), "error"); } };
  const slug = profile.data?.public_slug;
  return (
    <>
      <PageHeader title="Achievement locker" actions={<>
        <div className="w-44"><Select value={cat} onChange={setCat} options={vocab?.achievement_categories || []} placeholder="All categories" /></div>
        <button className="btn-secondary" onClick={() => openFile("/achievements/portfolio.pdf", "portfolio.pdf")}><Download className="h-4 w-4" />Portfolio PDF</button>
        <Link className="btn-primary" to="/achievements/new"><Plus className="h-4 w-4" />Add</Link></>} />
      <div className="card mb-4 flex flex-wrap items-center justify-between gap-3 text-sm">
        <span><Share2 className="mr-1 inline h-4 w-4" />Public portfolio: {profile.data?.public_portfolio_enabled ? "on" : "off"}
          {slug && <> · <a className="text-royal-600" href={`/p/${slug}`} target="_blank" rel="noopener noreferrer">{window.location.origin}/p/{slug}</a></>}
          <span className="block text-xs text-slate-500">The public page only shows achievements you mark as public. Certificates are never shown.</span></span>
        <button className="btn-secondary" onClick={togglePortfolio}>{profile.data?.public_portfolio_enabled ? "Disable" : "Enable"}</button>
      </div>
      {loading ? <Spinner /> : error ? <ErrorState message={error} onRetry={reload} /> : data!.length === 0 ? <Empty title="No achievements yet" /> :
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">{data!.map((a) => <AchievementCard key={a.id} a={a} actions={<>
          <Link className="text-royal-600" to={`/achievements/${a.id}/edit`}>Edit</Link>
          {a.certificate_document_id && <button className="text-royal-600" onClick={() => openFile(`/documents/${a.certificate_document_id}/preview`)}>Certificate</button>}
          <button className="text-red-600" onClick={() => del(a.id)}>Delete</button>{a.is_public && <span className="text-xs text-emerald-600">Public</span>}</>} />)}</div>}
    </>
  );
}
