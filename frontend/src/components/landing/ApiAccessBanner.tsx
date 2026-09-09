import { ArrowUpRight, MessageSquare, Key } from "lucide-react";

interface ApiAccessBannerProps {
  onRequestKey: () => void;
  onContactSpecialist: () => void;
}

export function ApiAccessBanner({ onRequestKey, onContactSpecialist }: ApiAccessBannerProps) {
  return (
    <section id="pricing" className="relative py-20 md:py-28">
      <div className="mx-auto max-w-[1400px] px-4 sm:px-6 lg:px-8">
        {/* Frosted Glass Banner Container */}
        <div className="relative overflow-hidden rounded-3xl border border-white/[0.12] bg-white/[0.025] p-8 text-center sm:p-14 md:p-20 shadow-[0_30px_90px_rgba(0,0,0,0.8),inset_0_1px_1px_rgba(255,255,255,0.15)] backdrop-blur-2xl">
          {/* Futuristic Radar Background Circles */}
          <div className="pointer-events-none absolute inset-0 flex items-center justify-center opacity-30">
            <div className="h-[650px] w-[650px] rounded-full border border-[#38BDF8]/20" />
            <div className="absolute h-[480px] w-[480px] rounded-full border border-[#38BDF8]/30 border-dashed animate-spin-slow" />
            <div className="absolute h-[320px] w-[320px] rounded-full border border-[#38BDF8]/40 shadow-[0_0_20px_rgba(56,189,248,0.2)]" />
            <div className="absolute h-[160px] w-[160px] rounded-full border border-[#38BDF8]/50" />
          </div>

          <div className="relative mx-auto max-w-3xl">
            {/* Frosted Pill */}
            <div className="inline-flex items-center gap-2 rounded-full border border-white/[0.12] bg-white/[0.04] px-4 py-1.5 text-[11px] font-semibold tracking-wider text-[#38BDF8] uppercase shadow-[0_8px_32px_0_rgba(0,0,0,0.37),inset_0_1px_1px_rgba(255,255,255,0.1)] backdrop-blur-2xl">
              <Key className="h-3.5 w-3.5" />
              <span className="tracking-[0.2em]">24/7 LIVE API ACCESS</span>
            </div>

            {/* Heading */}
            <h2 className="mt-6 font-display text-3xl font-extrabold tracking-tight text-white sm:text-4xl md:text-5xl">
              Connect your operations to real-time atmospheric intelligence
            </h2>

            {/* Subtitle */}
            <p className="mx-auto mt-5 max-w-2xl text-sm leading-relaxed text-[#94A3B8] sm:text-base">
              Seamlessly route sub-kilometer gRPC trajectories into CycloVision Mission Console. Continuous prediction matrix for hurricane warning centers, naval operations, and critical infrastructure.
            </p>

            {/* Frosted Action Buttons */}
            <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
              <button
                onClick={onRequestKey}
                className="group relative inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-[#0284C7] via-[#38BDF8] to-[#60A5FA] px-6 py-3.5 text-sm font-semibold text-[#090D14] shadow-[0_0_30px_rgba(56,189,248,0.45)] transition-all duration-300 hover:shadow-[0_0_45px_rgba(56,189,248,0.7)] hover:brightness-110 active:scale-[0.98]"
              >
                <span>Request API Key</span>
                <ArrowUpRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
              </button>

              <button
                onClick={onContactSpecialist}
                className="group inline-flex items-center gap-2 rounded-xl border border-white/[0.12] bg-white/[0.04] px-6 py-3.5 text-sm font-medium text-[#F8FAFC] shadow-[0_8px_32px_0_rgba(0,0,0,0.37),inset_0_1px_1px_rgba(255,255,255,0.12)] backdrop-blur-2xl transition-all duration-300 hover:border-[#38BDF8]/40 hover:bg-white/[0.08] hover:shadow-[0_0_25px_rgba(56,189,248,0.2)] active:scale-[0.98]"
              >
                <MessageSquare className="h-4 w-4 text-[#94A3B8] transition-colors group-hover:text-[#38BDF8]" />
                <span>Talk to Meteorology Specialist</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
