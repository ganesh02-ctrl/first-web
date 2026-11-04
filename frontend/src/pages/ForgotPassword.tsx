import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import AuthLayout from "../components/layout/AuthLayout";
import { Field } from "../components/common/ui";
import { errorMessage, send } from "../services/api";

export default function ForgotPassword() {
  const [email, setEmail] = useState(""); const [msg, setMsg] = useState(""); const [err, setErr] = useState("");
  const submit = async (e: FormEvent) => {
    e.preventDefault(); setErr("");
    try { await send("post", "/auth/forgot-password", { email });
      setMsg("If an account exists for that email, we've sent a reset link. Email has to be configured on the server for it to arrive."); }
    catch (x) { setErr(errorMessage(x)); }
  };
  return (
    <AuthLayout title="Forgot password">
      {msg ? <p className="text-sm">{msg}</p> : (
        <form onSubmit={submit} className="space-y-4">
          <Field label="Email"><input className="input" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} /></Field>
          {err && <p className="text-sm text-red-600">{err}</p>}
          <button className="btn-primary w-full">Send reset link</button>
        </form>)}
      <Link className="mt-4 block text-sm text-royal-600" to="/login">Back to sign in</Link>
    </AuthLayout>
  );
}
