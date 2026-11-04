import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import AuthLayout from "../components/layout/AuthLayout";
import { useAuth } from "../contexts/AuthContext";
import { errorMessage, send } from "../services/api";

export default function VerifyEmail() {
  const token = useSearchParams()[0].get("token") || "";
  const { reload } = useAuth();
  const [msg, setMsg] = useState("Verifying…"); const ran = useRef(false);
  useEffect(() => {
    if (ran.current) return; ran.current = true;
    if (!token) { setMsg("This verification link is missing its token."); return; }
    send("post", "/auth/verify-email", { token }).then(() => { setMsg("Your email is verified."); reload(); })
      .catch((e) => setMsg(errorMessage(e)));
  }, [token, reload]);
  return <AuthLayout title="Email verification"><p className="text-sm">{msg}</p><Link className="mt-4 block text-sm text-royal-600" to="/login">Continue</Link></AuthLayout>;
}
