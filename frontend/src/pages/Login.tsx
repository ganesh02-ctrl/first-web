import { FormEvent, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import AuthLayout from "../components/layout/AuthLayout";
import { Field } from "../components/common/ui";
import { useAuth } from "../contexts/AuthContext";
import { errorMessage } from "../services/api";

export default function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const from = (useLocation().state as any)?.from;
  const [email, setEmail] = useState(""); const [password, setPassword] = useState("");
  const [err, setErr] = useState(""); const [busy, setBusy] = useState(false);
  const submit = async (e: FormEvent) => {
    e.preventDefault(); setBusy(true); setErr("");
    try { const u = await login(email, password); nav(from || (u.role === "admin" ? "/admin" : "/dashboard")); }
    catch (x) { setErr(errorMessage(x)); } finally { setBusy(false); }
  };
  return (
    <AuthLayout title="Sign in">
      <form onSubmit={submit} className="space-y-4">
        <Field label="Email"><input className="input" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} /></Field>
        <Field label="Password"><input className="input" type="password" required value={password} onChange={(e) => setPassword(e.target.value)} /></Field>
        {err && <p className="text-sm text-red-600">{err}</p>}
        <button className="btn-primary w-full" disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button>
        <div className="flex justify-between text-sm"><Link className="text-royal-600" to="/forgot-password">Forgot password?</Link>
          <Link className="text-royal-600" to="/register">Create account</Link></div>
      </form>
    </AuthLayout>
  );
}
