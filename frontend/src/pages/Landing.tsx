import {
  Award,
  Bell,
  Calculator,
  FileLock2,
  GraduationCap,
  ShieldCheck,
} from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";

const features = [
  [
    GraduationCap,
    "Scholarship Hub",
    "Only admin-verified records with an official source and a last-verified date.",
  ],
  [
    Bell,
    "Deadline reminders",
    "In-app reminders at 30, 15, 7, 3 and 1 days. Email and SMS go out once they're configured.",
  ],
  [
    Calculator,
    "Master Semester Records",
    "Manage eight semesters with institution-configured, credit-weighted results.",
  ],
  [
    Award,
    "Achievement locker",
    "Keep a portfolio, download it as a PDF, and share it if you choose.",
  ],
  [
    FileLock2,
    "Document vault",
    "Private storage with a checklist of documents you still need.",
  ],
  [
    ShieldCheck,
    "Secure",
    "JWT sessions, hashed passwords, file content checks and rate limits.",
  ],
] as const;

export default function Landing() {
  const { user } = useAuth();
  const home = user
    ? user.role === "admin"
      ? "/admin"
      : "/dashboard"
    : "/register";

  return (
    <div className="min-h-screen">
      <header className="mx-auto flex max-w-6xl items-center justify-between p-6">
        <span className="text-xl font-bold text-navy-800 dark:text-white">
          SSS
        </span>
        <div className="flex gap-2">
          {!user && (
            <Link className="btn-secondary" to="/login">
              Sign in
            </Link>
          )}
          <Link className="btn-primary" to={home}>
            {user ? "Open app" : "Get started"}
          </Link>
        </div>
      </header>

      <section className="mx-auto max-w-4xl px-6 py-16 text-center">
        <h1 className="text-4xl font-bold text-navy-800 dark:text-white md:text-5xl">
          Student Support System
        </h1>
        <p className="mt-3 text-lg text-accent-500">
          Discover • Track • Calculate • Showcase
        </p>
        <p className="mx-auto mt-4 max-w-2xl text-slate-500">
          Find scholarships, track deadlines, calculate your grades and
          keep your achievements and documents in one place. Always
          confirm scholarship details on the official portal before you
          apply.
        </p>
      </section>

      <section className="mx-auto grid max-w-6xl gap-4 px-6 pb-16 md:grid-cols-3">
        {features.map(([Icon, title, description]) => (
          <div key={title} className="card">
            <Icon className="mb-3 h-6 w-6 text-royal-600" />
            <h3 className="font-semibold">{title}</h3>
            <p className="mt-1 text-sm text-slate-500">
              {description}
            </p>
          </div>
        ))}
      </section>
    </div>
  );
}
