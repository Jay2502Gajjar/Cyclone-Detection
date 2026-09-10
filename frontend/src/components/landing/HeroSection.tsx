import { Link } from "@tanstack/react-router";
import { ArrowUpRight } from "lucide-react";
import { ScrollReveal } from "./ScrollReveal";

export function HeroSection() {
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
            <span className="tracking-[0.2em]">ANALYSE · PREDICT · PREPARE</span>
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
            VAIYU bypasses traditional numerical simulation bottlenecks. Our globally scaled neural tensor network predicts tropical cyclogenesis, wind radii, and rapid intensification in 30-second intervals.
          </p>
        </ScrollReveal>

        {/* Frosted Glass CTA */}
        <ScrollReveal direction="up" delay={350} distance={20}>
          <div className="mt-10 flex items-center justify-center">
            <Link
              to="/dashboard"
              className="group relative inline-flex items-center gap-2.5 rounded-xl bg-gradient-to-r from-[#0284C7] via-[#38BDF8] to-[#60A5FA] px-8 py-4 text-base font-semibold text-[#090D14] shadow-[0_0_35px_rgba(56,189,248,0.5)] transition-all duration-300 hover:shadow-[0_0_50px_rgba(56,189,248,0.75)] hover:brightness-110 active:scale-[0.98]"
            >
              <span>Go to Dashboard</span>
              <ArrowUpRight className="h-5 w-5 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
            </Link>
          </div>
        </ScrollReveal>
      </div>
    </section>
  );
}
