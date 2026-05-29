import React from "react";
import Nav from "../components/Nav";
import Hero from "../components/Hero";
import Stats from "../components/Stats";
import Problem from "../components/Problem";
import AgentsShowcase from "../components/AgentsShowcase";
import DashboardPreview from "../components/DashboardPreview";
import ProofOfWork from "../components/ProofOfWork";
import EngineSection from "../components/EngineSection";
import Pricing from "../components/Pricing";
import Roadmap from "../components/Roadmap";
import FAQ from "../components/FAQ";
import Waitlist from "../components/Waitlist";
import Footer from "../components/Footer";
import CohortBar from "../components/CohortBar";
import { useReferralCapture } from "../lib/referral";

export default function LandingPage() {
  useReferralCapture();
  return (
    <>
      <Nav />
      <main className="relative z-10">
        <Hero />
        <Stats />
        <Problem />
        <AgentsShowcase />
        <DashboardPreview />
        <ProofOfWork />
        <EngineSection />
        <Pricing />
        <Roadmap />
        <FAQ />
        <Waitlist />
      </main>
      <Footer />
      <CohortBar />
    </>
  );
}
