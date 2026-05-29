import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "sonner";
import LandingPage from "./pages/LandingPage";
import DashboardLayout from "./pages/dashboard/DashboardLayout";
import Overview from "./pages/dashboard/Overview";
import AgentsPage from "./pages/dashboard/AgentsPage";
import ApprovalsPage from "./pages/dashboard/ApprovalsPage";
import RevenuePage from "./pages/dashboard/RevenuePage";
import ContentPage from "./pages/dashboard/ContentPage";

export default function App() {
  return (
    <div className="noise relative min-h-screen bg-bg text-ink" data-testid="app-root">
      <Toaster
        theme="dark"
        position="bottom-right"
        toastOptions={{
          style: {
            background: "#0C0C0C",
            border: "1px solid #00FF41",
            color: "#F3F4F6",
            fontFamily: "JetBrains Mono, monospace",
            borderRadius: 0,
          },
        }}
      />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/dashboard" element={<DashboardLayout />}>
            <Route index element={<Overview />} />
            <Route path="agents" element={<AgentsPage />} />
            <Route path="approvals" element={<ApprovalsPage />} />
            <Route path="revenue" element={<RevenuePage />} />
            <Route path="content" element={<ContentPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </div>
  );
}
