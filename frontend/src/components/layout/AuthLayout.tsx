import { ReactNode } from "react";
import { Link } from "react-router-dom";

export default function AuthLayout({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <div className="w-full max-w-md">
        <Link to="/" className="mb-6 block text-center text-2xl font-bold text-navy-800 dark:text-white">SSS</Link>
        <div className="card"><h1 className="mb-4 text-xl font-semibold">{title}</h1>{children}</div>
      </div>
    </div>
  );
}
