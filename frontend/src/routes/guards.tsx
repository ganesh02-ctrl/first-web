import { Navigate, Outlet, useLocation } from "react-router-dom";
import { Spinner } from "../components/common/ui";
import { useAuth } from "../contexts/AuthContext";

export function RequireAuth({ role }: { role?: "admin" | "student" }) {
  const { user, loading } = useAuth();
  const loc = useLocation();
  if (loading) return <Spinner />;
  if (!user) return <Navigate to="/login" state={{ from: loc.pathname }} replace />;
  if (role && user.role !== role) return <Navigate to={user.role === "admin" ? "/admin" : "/dashboard"} replace />;
  return <Outlet />;
}

export function GuestOnly() {
  const { user, loading } = useAuth();
  if (loading) return <Spinner />;
  if (user) return <Navigate to={user.role === "admin" ? "/admin" : "/dashboard"} replace />;
  return <Outlet />;
}
