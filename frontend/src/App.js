import React from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "sonner";
import LandingPage from "./pages/LandingPage";
import CheckoutSuccess from "./pages/CheckoutSuccess";
import DashboardLayout from "./pages/dashboard/DashboardLayout";
import Overview from "./pages/dashboard/Overview";
import AgentsPage from "./pages/dashboard/AgentsPage";
import SovereignPage from "./pages/dashboard/SovereignPage";
import ApprovalsPage from "./pages/dashboard/ApprovalsPage";
import RevenuePage from "./pages/dashboard/RevenuePage";
import ContentPage from "./pages/dashboard/ContentPage";
import ScoutPage from "./pages/dashboard/ScoutPage";
import DeploymentsPage from "./pages/dashboard/DeploymentsPage";
import BuildsPage from "./pages/dashboard/BuildsPage";
import AuditPage from "./pages/dashboard/AuditPage";
import BooksPage from "./pages/dashboard/BooksPage";
import ProposalsPage from "./pages/dashboard/ProposalsPage";
import SecretsPage from "./pages/dashboard/SecretsPage";
import CostPage from "./pages/dashboard/CostPage";
import ProofOfWorkPage from "./pages/dashboard/ProofOfWorkPage";
import AnalyticsPage from "./pages/dashboard/AnalyticsPage";
import DistillationPage from "./pages/dashboard/DistillationPage";
import AdvisorPage from "./pages/dashboard/AdvisorPage";
import CashAIPage from "./pages/dashboard/CashAIPage";
import LifelongPage from "./pages/dashboard/LifelongPage";

export default function App() {
  return (
      <div className="relative min-h-screen bg-bg text-ink" data-testid="app-root">
      <Toaster
        theme="dark"
        position="bottom-right"
        toastOptions={{
          style: {
            background: "#0f1423",
            border: "1px solid rgba(34,197,94,0.4)",
            color: "#f1f5f9",
            fontFamily: "Inter, system-ui, sans-serif",
            borderRadius: 10,
          },
        }}
      />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/checkout/success" element={<CheckoutSuccess />} />
          <Route path="/dashboard" element={<DashboardLayout />}>
            <Route index element={<Overview />} />
            <Route path="sovereign" element={<SovereignPage />} />
            <Route path="cash-ai" element={<CashAIPage />} />
            <Route path="lifelong" element={<LifelongPage />} />
            <Route path="agents" element={<AgentsPage />} />
            <Route path="approvals" element={<ApprovalsPage />} />
            <Route path="advisor" element={<AdvisorPage />} />
            <Route path="scout" element={<ScoutPage />} />
            <Route path="content" element={<ContentPage />} />
            <Route path="revenue" element={<RevenuePage />} />
            <Route path="books" element={<BooksPage />} />
            <Route path="deployments" element={<DeploymentsPage />} />
            <Route path="builds" element={<BuildsPage />} />
            <Route path="audit" element={<AuditPage />} />
            <Route path="proposals" element={<ProposalsPage />} />
            <Route path="proof-of-work" element={<ProofOfWorkPage />} />
            <Route path="analytics" element={<AnalyticsPage />} />
            <Route path="distillation" element={<DistillationPage />} />
            <Route path="cost" element={<CostPage />} />
            <Route path="secrets" element={<SecretsPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </div>
  );
}
