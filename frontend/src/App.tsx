import { Navigate, Route, Routes } from "react-router-dom";
import AppLayout from "./components/layout/AppLayout";
import { GuestOnly, RequireAuth } from "./routes/guards";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Register from "./pages/Register";
import ForgotPassword from "./pages/ForgotPassword";
import ResetPassword from "./pages/ResetPassword";
import VerifyEmail from "./pages/VerifyEmail";
import Dashboard from "./pages/Dashboard";
import Scholarships from "./pages/Scholarships";
import ScholarshipDetail from "./pages/ScholarshipDetail";
import Tracked from "./pages/Tracked";
import Applications from "./pages/Applications";
import MasterRecords from "./pages/MasterRecords";
import GradingPolicy from "./pages/admin/GradingPolicy";
import Achievements from "./pages/Achievements";
import AchievementForm from "./pages/AchievementForm";
import Documents from "./pages/Documents";
import Profile from "./pages/Profile";
import Notifications from "./pages/Notifications";
import SettingsPage from "./pages/Settings";
import PublicPortfolio from "./pages/PublicPortfolio";
import AdminDashboard from "./pages/admin/AdminDashboard";
import AdminScholarships from "./pages/admin/AdminScholarships";
import AdminScholarshipForm from "./pages/admin/AdminScholarshipForm";
import AdminStudents from "./pages/admin/AdminStudents";
import AdminReports from "./pages/admin/AdminReports";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/verify-email" element={<VerifyEmail />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route path="/p/:slug" element={<PublicPortfolio />} />

      <Route element={<GuestOnly />}>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
      </Route>

      <Route element={<RequireAuth />}>
        <Route element={<AppLayout />}>
          <Route path="/scholarships" element={<Scholarships />} />
          <Route
            path="/scholarships/:id"
            element={<ScholarshipDetail />}
          />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/notifications" element={<Notifications />} />

          <Route element={<RequireAuth role="student" />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/tracked" element={<Tracked />} />
            <Route path="/applications" element={<Applications />} />
            <Route
              path="/master-semesters"
              element={<MasterRecords />}
            />
            <Route path="/achievements" element={<Achievements />} />
            <Route
              path="/achievements/new"
              element={<AchievementForm />}
            />
            <Route
              path="/achievements/:id/edit"
              element={<AchievementForm />}
            />
            <Route path="/documents" element={<Documents />} />
            <Route path="/profile" element={<Profile />} />
          </Route>

          <Route path="/admin" element={<RequireAuth role="admin" />}>
            <Route index element={<AdminDashboard />} />
            <Route
              path="scholarships"
              element={<AdminScholarships />}
            />
            <Route
              path="scholarships/new"
              element={<AdminScholarshipForm />}
            />
            <Route
              path="scholarships/:id"
              element={<AdminScholarshipForm />}
            />
            <Route path="students" element={<AdminStudents />} />
            <Route path="reports" element={<AdminReports />} />
            <Route
              path="grading-policy"
              element={<GradingPolicy />}
            />
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
