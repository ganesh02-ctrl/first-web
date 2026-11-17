import {
  Award,
  Bell,
  BookMarked,
  ClipboardList,
  FileLock2,
  GraduationCap,
  LayoutDashboard,
  LogOut,
  Menu,
  Moon,
  Settings,
  Shield,
  Sun,
  User,
  Users,
  FileWarning,
  Library,
} from "lucide-react";
import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import { useTheme } from "../../contexts/ThemeContext";
import { get } from "../../services/api";
import { useApi } from "../../hooks/useApi";

const studentNav = [
  ["/dashboard", "Dashboard", LayoutDashboard],
  ["/scholarships", "Scholarships", GraduationCap],
  ["/tracked", "Tracked", BookMarked],
  ["/applications", "Applications", ClipboardList],
  ["/master-semesters", "MASTER SEMESTER RECORDS", Library],
  ["/achievements", "Achievements", Award],
  ["/documents", "Document Vault", FileLock2],
  ["/notifications", "Notifications", Bell],
  ["/profile", "Profile", User],
  ["/settings", "Settings", Settings],
] as const;

const adminNav = [
  ["/admin", "Admin Dashboard", Shield],
  ["/admin/scholarships", "Scholarships", GraduationCap],
  ["/admin/grading-policy", "Grading Policy", Library],
  ["/admin/students", "Students", Users],
  ["/admin/reports", "Reports & Logs", FileWarning],
] as const;

export default function AppLayout() {
  const { user, logout } = useAuth();
  const { dark, toggle } = useTheme();
  const nav = useNavigate();
  const [open, setOpen] = useState(false);

  const unread =
    useApi(
      () => get<{ count: number }>("/notifications/unread-count"),
      [],
    ).data?.count ?? 0;

  const items =
    user?.role === "admin"
      ? [
          ...adminNav,
          ["/settings", "Settings", Settings] as const,
        ]
      : studentNav;

  return (
    <div className="flex min-h-screen">
      <aside
        className={`fixed inset-y-0 left-0 z-30 w-64 transform bg-navy-900 text-slate-200 transition md:static md:translate-x-0 ${
          open ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="px-6 py-5">
          <p className="text-lg font-bold text-white">SSS</p>
          <p className="text-xs text-slate-400">
            Discover • Track • Calculate • Showcase
          </p>
        </div>

        <nav className="space-y-1 px-3">
          {items.map(([to, text, Icon]) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/admin"}
              onClick={() => setOpen(false)}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-3 py-2 text-sm ${
                  isActive
                    ? "bg-royal-600 text-white"
                    : "hover:bg-navy-700"
                }`
              }
            >
              <Icon className="h-4 w-4" />
              {text}
              {to === "/notifications" && unread > 0 && (
                <span className="ml-auto rounded-full bg-accent-500 px-2 text-xs">
                  {unread}
                </span>
              )}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3 dark:border-slate-800 dark:bg-slate-900">
          <button
            className="md:hidden"
            onClick={() => setOpen(!open)}
            aria-label="Menu"
          >
            <Menu />
          </button>

          <span className="text-sm text-slate-500">
            {user?.full_name || user?.email}
          </span>

          <div className="flex gap-2">
            <button
              className="btn-secondary"
              onClick={toggle}
              aria-label="Toggle theme"
            >
              {dark ? (
                <Sun className="h-4 w-4" />
              ) : (
                <Moon className="h-4 w-4" />
              )}
            </button>

            <button
              className="btn-secondary"
              onClick={async () => {
                await logout();
                nav("/login");
              }}
            >
              <LogOut className="h-4 w-4" />
              Sign out
            </button>
          </div>
        </header>

        {user && !user.email_verified && (
          <div className="bg-amber-50 px-4 py-2 text-sm text-amber-800">
            Your email is not verified. You can resend the link from
            Settings.
          </div>
        )}

        <main className="mx-auto w-full max-w-7xl flex-1 p-4 md:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
