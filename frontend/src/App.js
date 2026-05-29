import React from "react";
import { Toaster } from "sonner";
import Nav from "./components/Nav";
import Hero from "./components/Hero";
import Stats from "./components/Stats";
import Features from "./components/Features";
import Playground from "./components/Playground";
import DemoReport from "./components/DemoReport";
import Pricing from "./components/Pricing";
import Waitlist from "./components/Waitlist";
import Footer from "./components/Footer";

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
      <Nav />
      <main className="relative z-10">
        <Hero />
        <Stats />
        <Features />
        <Playground />
        <DemoReport />
        <Pricing />
        <Waitlist />
      </main>
      <Footer />
    </div>
  );
}
