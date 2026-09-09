import { useState } from "react";
import { LandingNav } from "./LandingNav";
import { HeroSection } from "./HeroSection";
import { PartnerBar } from "./PartnerBar";
import { CommandShowcase } from "./CommandShowcase";
import { EngineeringSpecs } from "./EngineeringSpecs";
import { BenchmarkTable } from "./BenchmarkTable";
import { ApiAccessBanner } from "./ApiAccessBanner";
import { LandingFooter } from "./LandingFooter";
import { AccessModal } from "./AccessModal";
import { ScrollProgressBar } from "./ScrollReveal";

export function LandingPage() {
  const [modalState, setModalState] = useState<{
    isOpen: boolean;
    type: "access" | "specs" | "key" | "specialist";
  }>({
    isOpen: false,
    type: "access",
  });

  const openModal = (type: "access" | "specs" | "key" | "specialist") => {
    setModalState({ isOpen: true, type });
  };

  const closeModal = () => {
    setModalState((prev) => ({ ...prev, isOpen: false }));
  };

  return (
    <div className="relative min-h-screen bg-[#06080D] text-[#F8FAFC] selection:bg-[#38BDF8] selection:text-[#090D14] overflow-x-hidden font-sans">
      {/* 1. Luminous Top Scroll Progress Bar */}
      <ScrollProgressBar />

      {/* 2. Expansive, Wide-Spread Planetary Light Fields & Nebulae */}
      <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden transform-gpu">
        {/* Top Center-Left Sky Cyan Flare */}
        <div className="absolute -top-[25%] left-1/2 -translate-x-1/2 h-[1000px] w-[1500px] rounded-full bg-gradient-to-b from-[#38BDF8]/20 via-[#0284C7]/14 to-transparent blur-[240px] transform-gpu" />

        {/* Top-Right Cybernetic Cobalt Aurora */}
        <div className="absolute top-[6%] -right-[22%] h-[1100px] w-[1100px] rounded-full bg-gradient-to-br from-[#1E40AF]/18 via-[#1D4ED8]/12 to-transparent blur-[260px] transform-gpu" />
        
        {/* Mid-Left Deep Pacific Indigo Nebula */}
        <div className="absolute top-[32%] -left-[24%] h-[1200px] w-[1200px] rounded-full bg-gradient-to-tr from-[#1E3A8A]/22 via-[#1E40AF]/15 to-transparent blur-[280px] transform-gpu" />

        {/* Mid-Right Luminous Turquoise Cyclone Bloom */}
        <div className="absolute top-[52%] -right-[24%] h-[1200px] w-[1200px] rounded-full bg-gradient-to-tl from-[#06B6D4]/18 via-[#0284C7]/15 to-transparent blur-[270px] transform-gpu" />
        
        {/* Lower-Center Electric Sky Horizon */}
        <div className="absolute top-[72%] left-1/2 -translate-x-1/2 h-[950px] w-[1500px] rounded-full bg-gradient-to-t from-[#38BDF8]/16 via-[#0284C7]/10 to-transparent blur-[260px] transform-gpu" />

        {/* Bottom Planetary Atmosphere Base */}
        <div className="absolute -bottom-[20%] left-1/2 -translate-x-1/2 h-[850px] w-[1600px] rounded-full bg-gradient-to-t from-[#1D4ED8]/18 via-[#0284C7]/12 to-transparent blur-[280px] transform-gpu" />

        {/* Soft Cosmic Micro-Dust & Starfield Accents */}
        <div className="absolute inset-0 bg-[radial-gradient(#38BDF8_1px,transparent_1px)] [background-size:80px_80px] opacity-[0.07] [mask-image:radial-gradient(ellipse_70%_70%_at_50%_50%,#000_60%,transparent_100%)]" />
      </div>

      <div className="relative z-10 flex flex-col min-h-screen">
        {/* Top Navigation Bar */}
        <LandingNav onRequestAccess={() => openModal("access")} />

        {/* Main Content Sections */}
        <main className="flex-1">
          {/* Hero Section */}
          <HeroSection onOpenSpecs={() => openModal("specs")} />

          {/* Partner Meteorological Agencies Bar */}
          <PartnerBar />

          {/* Real-Time Command & Control Showcase */}
          <CommandShowcase />

          {/* Engineering Specifications */}
          <EngineeringSpecs />

          {/* Benchmark Disruption Table */}
          <BenchmarkTable />

          {/* Live API Access CTA Banner */}
          <ApiAccessBanner
            onRequestKey={() => openModal("key")}
            onContactSpecialist={() => openModal("specialist")}
          />
        </main>

        {/* Footer */}
        <LandingFooter />
      </div>

      {/* Interactive Access Modal */}
      <AccessModal
        isOpen={modalState.isOpen}
        type={modalState.type}
        onClose={closeModal}
      />
    </div>
  );
}
