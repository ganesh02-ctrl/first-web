import { FormEvent, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import AuthLayout from "../components/layout/AuthLayout";
import { Field } from "../components/common/ui";
import { errorMessage, send } from "../services/api";

export default function ResetPassword() {
  const token = useSearchParams()[0].get("token") || "";
  const [password, setPassword] = useState(""); const [done, setDone] = useState(false); const [err, setErr] = useState("");
  const submit = async (e: FormEvent) => {
    e.preventDefault(); setErr("");
    try { await send("post", "/auth/reset-password", { token, password }); setDone(true); } catch (x) { setErr(errorMessage(x)); }
  };
  return (
    <AuthLayout title="Choose a new password">
      {done ? <p className="text-sm">Password updated. <Link className="text-royal-600" to="/login">Sign in</Link></p> : (
        <form onSubmit={submit} className="space-y-4">
          {!token && <p className="text-sm text-red-600">This reset link is missing its token.</p>}
          <Field label="New password"><input className="input" type="password" required minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} /></Field>
          {err && <p className="text-sm text-red-600">{err}</p>}
          <button className="btn-primary w-full" disabled={!token}>Update password</button>
        </form>)}
    </AuthLayout>
  );
}
