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
    <div className="relative min-h-screen bg-[#0B0D13] text-[#F8FAFC] selection:bg-[#38BDF8] selection:text-[#090D14] overflow-x-hidden font-sans">
      {/* Ambient Glassmorphic Background Glow Orbs */}
      <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
        {/* Top cyan/cobalt light cone */}
        <div className="absolute -top-[20%] left-1/2 -translate-x-1/2 h-[750px] w-[1200px] rounded-full bg-gradient-to-b from-[#38BDF8]/20 via-[#1D4ED8]/15 to-transparent blur-[160px]" />
        
        {/* Middle ambient cobalt radial bloom */}
        <div className="absolute top-[35%] -left-[10%] h-[700px] w-[700px] rounded-full bg-[#1E40AF]/12 blur-[180px]" />
        <div className="absolute top-[50%] -right-[10%] h-[800px] w-[800px] rounded-full bg-[#0284C7]/12 blur-[200px]" />
        
        {/* Bottom CTA teal/cyan glow */}
        <div className="absolute bottom-[10%] left-1/2 -translate-x-1/2 h-[600px] w-[1000px] rounded-full bg-gradient-to-t from-[#0284C7]/15 via-[#38BDF8]/10 to-transparent blur-[160px]" />

        {/* Cybernetic geometric grid overlay */}
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#1E293B0A_1px,transparent_1px),linear-gradient(to_bottom,#1E293B0A_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_70%,transparent_100%)] opacity-60" />
      </div>

      <div className="relative z-10 flex flex-col min-h-screen">
        {/* 1. Frosted Top Navigation Bar */}
        <LandingNav onRequestAccess={() => openModal("access")} />

        {/* Main Content Sections */}
        <main className="flex-1">
          {/* 2. Hero Section */}
          <HeroSection onOpenSpecs={() => openModal("specs")} />

          {/* 3. Frosted Partner Meteorological Agencies Bar */}
          <PartnerBar />

          {/* 4. Glassmorphic Real-Time Command & Control Showcase */}
          <CommandShowcase />

          {/* 5. Frosted Engineering Specifications */}
          <EngineeringSpecs />

          {/* 6. Benchmark Disruption Glass Table */}
          <BenchmarkTable />

          {/* 7. Frosted Live API Access CTA Banner */}
          <ApiAccessBanner
            onRequestKey={() => openModal("key")}
            onContactSpecialist={() => openModal("specialist")}
          />
        </main>

        {/* 8. Glassmorphic Footer */}
        <LandingFooter />
      </div>

      {/* Interactive Glass Access Modal */}
      <AccessModal
        isOpen={modalState.isOpen}
        type={modalState.type}
        onClose={closeModal}
      />
    </div>
  );
}
