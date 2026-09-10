import { Link } from "@tanstack/react-router";
import { ArrowUpRight, FileText } from "lucide-react";
import { ScrollReveal } from "./ScrollReveal";

interface HeroSectionProps {
  onOpenSpecs: () => void;
}

export function HeroSection({ onOpenSpecs }: HeroSectionProps) {
  return (
    <section className="relative overflow-hidden pt-16 pb-20 md:pt-24 md:pb-28">
      <div className="relative mx-auto max-w-5xl px-4 text-center sm:px-6 lg:px-8">
        {/* Frosted Glass Core Badge */}
        <ScrollReveal direction="down" delay={50} distance={20}>
          <div className="inline-flex items-center gap-2.5 rounded-full border border-white/[0.12] bg-white/[0.04] px-4 py-1.5 text-[11px] font-semibold tracking-wider text-[#38BDF8] uppercase shadow-[0_8px_32px_0_rgba(0,0,0,0.37),inset_0_1px_1px_rgba(255,255,255,0.15)] backdrop-blur-2xl transition-all duration-300 hover:border-[#38BDF8]/50 hover:shadow-[0_0_20px_rgba(56,189,248,0.25)]">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#38BDF8] opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-[#38BDF8]" />
            </span>
            <span className="tracking-[0.2em]">SATELLITE AI CORE V3.2</span>
          </div>
        </ScrollReveal>

        {/* Main Headline with Glass Shimmer */}
        <ScrollReveal direction="up" delay={150} distance={28}>
          <h1 className="mt-8 font-display text-4xl font-extrabold tracking-tight text-white sm:text-5xl md:text-6xl lg:text-[66px] lg:leading-[1.12]">
            Sub-kilometer cyclone forecasting <br className="hidden sm:inline" />
            powered by{" "}
            <span className="relative inline-block">
              <span className="bg-gradient-to-r from-white via-[#BAE6FD] to-[#38BDF8] bg-clip-text text-transparent drop-shadow-[0_0_30px_rgba(56,189,248,0.35)]">
                continuous satellite AI
              </span>
            </span>
          </h1>
        </ScrollReveal>

        {/* Subtitle */}
        <ScrollReveal direction="up" delay={250} distance={24}>
          <p className="mx-auto mt-6 max-w-3xl text-sm leading-relaxed text-[#94A3B8] sm:text-base md:text-lg">
            CycloVision bypasses traditional numerical simulation bottlenecks. Our globally scaled neural tensor network predicts tropical cyclogenesis, wind radii, and rapid intensification in 30-second intervals.
          </p>
        </ScrollReveal>

        {/* Frosted Glass CTAs */}
        <ScrollReveal direction="up" delay={350} distance={20}>
          <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
            <Link
              to="/dashboard"
              className="group relative inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-[#0284C7] via-[#38BDF8] to-[#60A5FA] px-6 py-3.5 text-sm font-semibold text-[#090D14] shadow-[0_0_30px_rgba(56,189,248,0.45)] transition-all duration-300 hover:shadow-[0_0_45px_rgba(56,189,248,0.7)] hover:brightness-110 active:scale-[0.98]"
            >
              <span>View Live Telemetry</span>
              <ArrowUpRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
            </Link>

            <button
              onClick={onOpenSpecs}
              className="group inline-flex items-center gap-2 rounded-xl border border-white/[0.12] bg-white/[0.04] px-6 py-3.5 text-sm font-medium text-[#F8FAFC] shadow-[0_8px_32px_0_rgba(0,0,0,0.37),inset_0_1px_1px_rgba(255,255,255,0.12)] backdrop-blur-2xl transition-all duration-300 hover:border-[#38BDF8]/40 hover:bg-white/[0.08] hover:shadow-[0_0_25px_rgba(56,189,248,0.2)] active:scale-[0.98]"
            >
              <FileText className="h-4 w-4 text-[#94A3B8] transition-colors group-hover:text-[#38BDF8]" />
              <span>Read Technical Spec</span>
            </button>
          </div>
        </ScrollReveal>
      </div>
    </section>
  );
}
