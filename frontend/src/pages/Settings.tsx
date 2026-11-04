import { FormEvent, useState } from "react";
import ScaleEditor from "../components/academic/ScaleEditor";
import { Field, Modal, PageHeader } from "../components/common/ui";
import { useAuth } from "../contexts/AuthContext";
import { useTheme } from "../contexts/ThemeContext";
import { useToast } from "../contexts/ToastContext";
import { useApi } from "../hooks/useApi";
import { errorMessage, get, send } from "../services/api";
import type { Scale } from "../types";

export default function SettingsPage() {
  const { user, setSession } = useAuth(); const { dark, toggle } = useTheme(); const { notify } = useToast();
  const prefs = useApi(() => get<any>("/notifications/preferences"));
  const scales = useApi(() => get<Scale[]>("/academics/scales"));
  const [pw, setPw] = useState({ current_password: "", new_password: "" });
  const [editing, setEditing] = useState<Scale | "new" | null>(null);
  const run = async (fn: () => Promise<any>, ok: string) => { try { const r = await fn(); notify(ok); return r ?? true; } catch (e) { notify(errorMessage(e), "error"); return null; } };

  const savePrefs = (patch: any) => run(() => send("put", "/notifications/preferences", { ...prefs.data, ...patch }), "Preferences saved").then(() => prefs.reload());
  const changePw = async (e: FormEvent) => { e.preventDefault();
    const d = await run(() => send<any>("post", "/auth/change-password", pw), "Password changed");
    if (d && d.access_token) { setSession(d); setPw({ current_password: "", new_password: "" }); } };
  const saveScale = async (body: any) => {
    const ok = await run(() => editing === "new" ? send("post", "/academics/scales", body) : send("put", `/academics/scales/${(editing as Scale).id}`, body), "Scale saved");
    if (ok) { setEditing(null); scales.reload(); } };
  const p = prefs.data;
  return (
    <>
      <PageHeader title="Settings" />
      <div className="grid gap-4 lg:grid-cols-2">
        <div className="card space-y-3"><h2 className="font-semibold">Appearance & account</h2>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={dark} onChange={toggle} />Dark mode</label>
          <p className="text-sm">Email: {user?.email} {user?.email_verified ? "(verified)" : <button className="text-royal-600" onClick={() => run(() => send("post", "/auth/resend-verification"), "Request processed")}>Resend verification</button>}</p>
        </div>
        {p && <div className="card space-y-2 text-sm"><h2 className="font-semibold">Notifications</h2>
          {[["in_app_enabled", "In-app"], ["email_enabled", "Email (needs SMTP on the server)"], ["sms_enabled", "SMS (needs an SMS provider and a phone number in your profile)"],
            ["deadline_reminders", "Deadline reminders"], ["application_updates", "Application updates"]].map(([k, t]) =>
            <label key={k} className="flex items-center gap-2"><input type="checkbox" checked={p[k]} onChange={(e) => savePrefs({ [k]: e.target.checked })} />{t}</label>)}
          <div><span className="label">Remind me before the deadline (days)</span><div className="flex gap-3">{[30, 15, 7, 3, 1].map((d) =>
            <label key={d} className="flex items-center gap-1"><input type="checkbox" checked={p.reminder_days.includes(d)}
              onChange={(e) => savePrefs({ reminder_days: e.target.checked ? [...p.reminder_days, d] : p.reminder_days.filter((x: number) => x !== d) })} />{d}</label>)}</div></div>
        </div>}
        <form onSubmit={changePw} className="card space-y-3"><h2 className="font-semibold">Change password</h2>
          <Field label="Current password"><input className="input" type="password" required value={pw.current_password} onChange={(e) => setPw({ ...pw, current_password: e.target.value })} /></Field>
          <Field label="New password"><input className="input" type="password" required minLength={8} value={pw.new_password} onChange={(e) => setPw({ ...pw, new_password: e.target.value })} /></Field>
          <button className="btn-primary">Update password</button><p className="text-xs text-slate-500">Changing your password signs you out on every other device.</p></form>
        <div className="card space-y-2 text-sm"><div className="flex justify-between"><h2 className="font-semibold">Grading scales</h2>
          <button className="btn-secondary" onClick={() => setEditing("new")}>New scale</button></div>
          {scales.data?.length === 0 && <p className="text-slate-500">No scales yet. Add your university's official scale.</p>}
          {scales.data?.map((s) => <div key={s.id} className="flex justify-between"><span>{s.name} ({s.grades.map((g) => `${g.label}=${g.grade_point}`).join(", ")}){s.is_template ? " · shared" : ""}</span>
            {(s.is_owned || user?.role === "admin") && <span className="space-x-2"><button className="text-royal-600" onClick={() => setEditing(s)}>Edit</button>
              <button className="text-red-600" onClick={() => confirm("Delete scale?") && run(() => send("delete", `/academics/scales/${s.id}`), "Deleted").then(() => scales.reload())}>Delete</button></span>}</div>)}
        </div>
      </div>
      {editing && <Modal title="Grading scale" onClose={() => setEditing(null)}>
        <ScaleEditor initial={editing === "new" ? undefined : editing} allowTemplate={user?.role === "admin"} onSave={saveScale} /></Modal>}
    </>
  );
}
