import { useState } from "react";
import { Link } from "@tanstack/react-router";
import { ArrowUpRight, Activity, Radio, Compass, ShieldAlert, Cpu, Sparkles } from "lucide-react";
import satelliteCycloneImg from "@/assets/satellite-cyclone.jpg";

export function CommandShowcase() {
  return (
    <section id="telemetry" className="relative py-20 md:py-28">
      {/* Dynamic Localized Glass Refraction Glow */}
      <div className="pointer-events-none absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 h-[550px] w-[850px] rounded-full bg-gradient-to-tr from-[#0284C7]/15 via-[#38BDF8]/10 to-[#1D4ED8]/12 blur-[140px]" />

      <div className="relative mx-auto max-w-[1400px] px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center">
          <div className="inline-flex items-center gap-2 rounded-full border border-white/[0.12] bg-white/[0.04] px-4 py-1.5 text-[11px] font-semibold tracking-wider text-[#38BDF8] uppercase shadow-[0_8px_32px_0_rgba(0,0,0,0.37),inset_0_1px_1px_rgba(255,255,255,0.1)] backdrop-blur-2xl">
            <Activity className="h-3.5 w-3.5" />
            <span className="tracking-[0.2em]">CRITICAL TELEMETRY STAGE</span>
          </div>

          <h2 className="mt-5 font-display text-3xl font-extrabold tracking-tight text-white sm:text-4xl md:text-5xl">
            Real-time Command & Control Dashboard
          </h2>

          <p className="mx-auto mt-4 max-w-2xl text-sm leading-relaxed text-[#94A3B8] sm:text-base">
            Status: Active operational feed from Super Typhoon Mawar. Intersected via geostationary microwave and physical wind ensemble projection.
          </p>
        </div>

        {/* Frosted Glass Outer Housing Frame */}
        <div className="mt-14 overflow-hidden rounded-3xl border border-white/[0.12] bg-white/[0.02] shadow-[0_25px_70px_-15px_rgba(0,0,0,0.7),inset_0_1px_1px_rgba(255,255,255,0.12)] backdrop-blur-2xl">
          {/* Frame Top Header */}
          <div className="flex flex-wrap items-center justify-between border-b border-white/[0.08] bg-white/[0.03] px-5 py-3.5 backdrop-blur-xl sm:px-7">
            <div className="flex items-center gap-4">
              {/* Terminal Traffic Status Dots */}
              <div className="flex items-center gap-1.5">
                <span className="h-2.5 w-2.5 rounded-full bg-[#EF4444] shadow-[0_0_8px_#EF4444]" />
                <span className="h-2.5 w-2.5 rounded-full bg-[#F59E0B] shadow-[0_0_8px_#F59E0B]" />
                <span className="h-2.5 w-2.5 rounded-full bg-[#10B981] shadow-[0_0_8px_#10B981]" />
              </div>

              <div className="hidden h-4 w-px bg-white/[0.1] sm:block" />

              <span className="font-display text-[11px] font-semibold tracking-wider text-[#94A3B8]">
                ACTUAL TELEMETRY: <span className="text-white font-mono">27°54'N 128°03'E</span>
              </span>
            </div>

            <div className="flex items-center gap-2">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#10B981] opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-[#10B981]" />
              </span>
              <span className="font-display text-[11px] font-medium tracking-wider text-[#10B981]">
                GEOSTATIONARY SATELLITE OVERLAY
              </span>
            </div>
          </div>

          {/* Frosted Bento Grid */}
          <div className="grid gap-6 p-4 sm:p-6 lg:grid-cols-2 lg:p-8">
            {/* Left Card: Microwave Spectrometry */}
            <div className="group relative flex flex-col justify-between rounded-2xl border border-white/[0.08] bg-white/[0.03] p-5 backdrop-blur-xl transition-all duration-300 hover:border-[#38BDF8]/40 hover:bg-white/[0.05] hover:shadow-[0_0_30px_rgba(56,189,248,0.15)]">
              <div>
                <div className="flex items-center justify-between pb-3.5 border-b border-white/[0.06]">
                  <div className="flex items-center gap-2.5">
                    <div className="flex h-6 w-6 items-center justify-center rounded-md bg-[#38BDF8]/10 text-[#38BDF8]">
                      <Radio className="h-3.5 w-3.5" />
                    </div>
                    <span className="font-display text-xs font-bold tracking-wider text-white uppercase">
                      MICROWAVE SPECTROMETRY (183GHz)
                    </span>
                  </div>
                  <span className="rounded-full bg-[#38BDF8]/10 px-2.5 py-0.5 font-display text-[10px] font-semibold text-[#38BDF8] border border-[#38BDF8]/30 shadow-[0_0_10px_rgba(56,189,248,0.2)]">
                    89 GHz
                  </span>
                </div>

                {/* Radar Image Visual */}
                <div className="relative mt-4 aspect-[16/10] overflow-hidden rounded-xl border border-white/[0.08] bg-[#07090E]">
                  <img
                    src={satelliteCycloneImg}
                    alt="Microwave satellite cyclone scan"
                    className="h-full w-full object-cover opacity-90 transition-transform duration-700 group-hover:scale-105"
                  />
                  
                  {/* Radar HUD overlay */}
                  <div className="absolute inset-0 bg-gradient-to-tr from-[#0284C7]/20 via-transparent to-[#F43F5E]/20 mix-blend-screen pointer-events-none" />
                  <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <div className="h-48 w-48 rounded-full border border-[#38BDF8]/30 border-dashed animate-spin-slow" />
                    <div className="absolute h-32 w-32 rounded-full border border-[#38BDF8]/40 shadow-[0_0_15px_rgba(56,189,248,0.2)]" />
                    <div className="absolute h-16 w-16 rounded-full border border-[#EF4444]/60 bg-[#EF4444]/10 animate-pulse" />
                    <div className="absolute h-1.5 w-1.5 rounded-full bg-white shadow-[0_0_12px_#FFFFFF]" />
                  </div>

                  {/* Glassmorphic Corner Indicators */}
                  <div className="absolute bottom-2.5 left-2.5 rounded-lg border border-white/[0.1] bg-[#0B0D13]/70 px-2.5 py-1 text-[9px] font-mono text-[#94A3B8] backdrop-blur-md">
                    SENSOR: AMSU-A / CH 14
                  </div>
                  <div className="absolute bottom-2.5 right-2.5 rounded-lg border border-[#38BDF8]/30 bg-[#0B0D13]/70 px-2.5 py-1 text-[9px] font-mono text-[#38BDF8] backdrop-blur-md">
                    RETICLE: EYE LOCKED
                  </div>
                </div>
              </div>

              {/* Bottom Metrics with Frosted Glass */}
              <div className="mt-5 grid grid-cols-2 gap-3 border-t border-white/[0.06] pt-4">
                <div className="rounded-xl border border-white/[0.06] bg-white/[0.025] p-3.5 backdrop-blur-md">
                  <div className="font-display text-[10px] font-medium tracking-wider text-[#94A3B8] uppercase">
                    PEAK SUSTAINED WIND
                  </div>
                  <div className="mt-1 font-display text-2xl font-bold tracking-tight text-white sm:text-3xl">
                    165 <span className="text-sm font-normal text-[#94A3B8]">kts</span>
                  </div>
                  <div className="mt-1 text-[11px] text-[#10B981] font-medium flex items-center gap-1">
                    <span>↑</span> +12 kts past 6 hrs
                  </div>
                </div>

                <div className="rounded-xl border border-white/[0.06] bg-white/[0.025] p-3.5 backdrop-blur-md">
                  <div className="font-display text-[10px] font-medium tracking-wider text-[#94A3B8] uppercase">
                    MINIMUM PRESSURE
                  </div>
                  <div className="mt-1 font-display text-2xl font-bold tracking-tight text-white sm:text-3xl">
                    898 <span className="text-sm font-normal text-[#94A3B8]">mb</span>
                  </div>
                  <div className="mt-1 text-[11px] text-[#38BDF8] font-medium">
                    Rapid Deepening Phase
                  </div>
                </div>
              </div>
            </div>

            {/* Right Card: Multi-Ensemble Track Path */}
            <div className="group relative flex flex-col justify-between rounded-2xl border border-white/[0.08] bg-white/[0.03] p-5 backdrop-blur-xl transition-all duration-300 hover:border-[#38BDF8]/40 hover:bg-white/[0.05] hover:shadow-[0_0_30px_rgba(56,189,248,0.15)]">
              <div>
                <div className="flex items-center justify-between pb-3.5 border-b border-white/[0.06]">
                  <div className="flex items-center gap-2.5">
                    <div className="flex h-6 w-6 items-center justify-center rounded-md bg-[#38BDF8]/10 text-[#38BDF8]">
                      <Compass className="h-3.5 w-3.5" />
                    </div>
                    <span className="font-display text-xs font-bold tracking-wider text-white uppercase">
                      MULTI-ENSEMBLE TRACK PATH
                    </span>
                  </div>
                  <span className="rounded-full bg-[#10B981]/10 px-2.5 py-0.5 font-display text-[10px] font-semibold text-[#10B981] border border-[#10B981]/30 shadow-[0_0_10px_rgba(16,185,129,0.2)]">
                    Confidence: 98.4%
                  </span>
                </div>

                {/* Trajectory Vector Visual */}
                <div className="relative mt-4 aspect-[16/10] overflow-hidden rounded-xl border border-white/[0.08] bg-[#07090E]">
                  <svg className="h-full w-full opacity-80" viewBox="0 0 500 300">
                    <defs>
                      <linearGradient id="glassTrackGrad" x1="0%" y1="100%" x2="100%" y2="0%">
                        <stop offset="0%" stopColor="#38BDF8" stopOpacity="0.3" />
                        <stop offset="60%" stopColor="#38BDF8" stopOpacity="0.9" />
                        <stop offset="100%" stopColor="#60A5FA" stopOpacity="1" />
                      </linearGradient>
                      <filter id="glassGlow">
                        <feGaussianBlur stdDeviation="3.5" result="coloredBlur"/>
                        <feMerge>
                          <feMergeNode in="coloredBlur"/>
                          <feMergeNode in="SourceGraphic"/>
                        </feMerge>
                      </filter>
                    </defs>

                    {/* Ocean Grid Lines */}
                    <pattern id="glassGrid" width="40" height="40" patternUnits="userSpaceOnUse">
                      <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1E293B" strokeWidth="0.8" strokeOpacity="0.5" />
                    </pattern>
                    <rect width="100%" height="100%" fill="url(#glassGrid)" />

                    {/* Coastal Outline Contours */}
                    <path
                      d="M 20 220 Q 60 180 110 200 T 180 140 T 260 120 T 320 80 T 420 50"
                      fill="none"
                      stroke="#334155"
                      strokeWidth="1.5"
                      opacity="0.7"
                    />

                    {/* Multi Ensemble Probabilistic Cone */}
                    <path
                      d="M 120 240 Q 220 180 340 90 L 370 70 Q 240 160 120 240 Z"
                      fill="#38BDF8"
                      fillOpacity="0.1"
                    />

                    {/* Main Trajectory Projected Arc */}
                    <path
                      d="M 120 240 Q 230 180 360 80"
                      fill="none"
                      stroke="url(#glassTrackGrad)"
                      strokeWidth="3.5"
                      filter="url(#glassGlow)"
                      strokeDasharray="6 3"
                    />

                    {/* Historical Track Solid */}
                    <path
                      d="M 40 280 Q 80 260 120 240"
                      fill="none"
                      stroke="#38BDF8"
                      strokeWidth="3"
                    />

                    {/* Vortex Streamlines around Current Position */}
                    <circle cx="120" cy="240" r="28" fill="none" stroke="#38BDF8" strokeWidth="1" strokeDasharray="3 3" opacity="0.6" />
                    <circle cx="120" cy="240" r="14" fill="#38BDF8" fillOpacity="0.25" />
                    <circle cx="120" cy="240" r="4" fill="#38BDF8" />

                    {/* Forecast Target Pings */}
                    <circle cx="260" cy="150" r="6" fill="#60A5FA" filter="url(#glassGlow)" />
                    <circle cx="260" cy="150" r="16" fill="none" stroke="#60A5FA" strokeWidth="1" opacity="0.6" />

                    <circle cx="360" cy="80" r="8" fill="#F43F5E" filter="url(#glassGlow)" />
                    <circle cx="360" cy="80" r="22" fill="none" stroke="#F43F5E" strokeWidth="1.2" opacity="0.8" />
                  </svg>

                  {/* Target Label HUD with Frosted Sheen */}
                  <div className="absolute top-1/2 left-1/2 -translate-x-12 -translate-y-6 rounded-xl border border-white/[0.15] bg-[#0B0D13]/85 px-3 py-2 shadow-2xl backdrop-blur-xl">
                    <div className="flex items-center gap-1.5">
                      <span className="h-2 w-2 rounded-full bg-[#EF4444] shadow-[0_0_8px_#EF4444] animate-ping" />
                      <span className="font-display text-[10px] font-bold text-white tracking-wide">
                        STORM EYE: 165 kts / 898 mb
                      </span>
                    </div>
                    <div className="font-mono text-[9px] text-[#94A3B8] mt-0.5">
                      27°54'N 128°03'E
                    </div>
                  </div>
                </div>
              </div>

              {/* Bottom Metrics with Frosted Glass */}
              <div className="mt-5 grid grid-cols-2 gap-3 border-t border-white/[0.06] pt-4">
                <div className="rounded-xl border border-white/[0.06] bg-white/[0.025] p-3.5 backdrop-blur-md">
                  <div className="font-display text-[10px] font-medium tracking-wider text-[#94A3B8] uppercase">
                    HORIZONTAL RESOLUTION
                  </div>
                  <div className="mt-1 font-display text-2xl font-bold tracking-tight text-white sm:text-3xl">
                    375 <span className="text-sm font-normal text-[#94A3B8]">meters</span>
                  </div>
                  <div className="mt-1 text-[11px] text-[#38BDF8] font-medium">
                    Sub-Kilometer Accuracy
                  </div>
                </div>

                <div className="rounded-xl border border-white/[0.06] bg-white/[0.025] p-3.5 backdrop-blur-md">
                  <div className="font-display text-[10px] font-medium tracking-wider text-[#94A3B8] uppercase">
                    PROPAGATION PRECISION
                  </div>
                  <div className="mt-1 font-display text-2xl font-bold tracking-tight text-white sm:text-3xl">
                    7.2 <span className="text-sm font-normal text-[#94A3B8]">meters</span>
                  </div>
                  <div className="mt-1 text-[11px] text-[#10B981] font-medium">
                    Turbulent Layer Model
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Frosted Bottom Action Strip */}
          <div className="flex flex-wrap items-center justify-between border-t border-white/[0.08] bg-white/[0.02] px-6 py-4 backdrop-blur-xl">
            <div className="text-xs text-[#94A3B8]">
              Operating on global continuous neural tensor stream • Model Latency: <span className="text-white font-mono font-medium">42ms</span>
            </div>
            <Link
              to="/dashboard"
              className="inline-flex items-center gap-1.5 font-display text-xs font-semibold text-[#38BDF8] hover:text-[#60A5FA] transition-colors"
            >
              <span>Launch Full Command Console</span>
              <ArrowUpRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
