import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import AuthLayout from "../components/layout/AuthLayout";
import { Field } from "../components/common/ui";
import { useAuth } from "../contexts/AuthContext";
import { useToast } from "../contexts/ToastContext";
import { errorMessage } from "../services/api";

export default function Register() {
  const { register } = useAuth(); const { notify } = useToast(); const nav = useNavigate();
  const [f, setF] = useState({ full_name: "", email: "", phone: "", password: "" });
  const [err, setErr] = useState(""); const [busy, setBusy] = useState(false);
  const set = (k: keyof typeof f) => (e: any) => setF({ ...f, [k]: e.target.value });
  const submit = async (e: FormEvent) => {
    e.preventDefault(); setBusy(true); setErr("");
    try { await register({ ...f, phone: f.phone || undefined }); notify("Account created"); nav("/dashboard"); }
    catch (x) { setErr(errorMessage(x)); } finally { setBusy(false); }
  };
  return (
    <AuthLayout title="Create your account">
      <form onSubmit={submit} className="space-y-4">
        <Field label="Full name"><input className="input" required minLength={2} value={f.full_name} onChange={set("full_name")} /></Field>
        <Field label="Email"><input className="input" type="email" required value={f.email} onChange={set("email")} /></Field>
        <Field label="Phone (optional)"><input className="input" value={f.phone} onChange={set("phone")} /></Field>
        <Field label="Password"><input className="input" type="password" required minLength={8} value={f.password} onChange={set("password")} /></Field>
        <p className="text-xs text-slate-500">At least 8 characters, with an uppercase letter, a lowercase letter and a digit.</p>
        {err && <p className="text-sm text-red-600">{err}</p>}
        <button className="btn-primary w-full" disabled={busy}>{busy ? "Creating…" : "Create account"}</button>
        <p className="text-center text-sm">Already registered? <Link className="text-royal-600" to="/login">Sign in</Link></p>
      </form>
    </AuthLayout>
  );
}
