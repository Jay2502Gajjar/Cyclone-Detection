import { Link } from "@tanstack/react-router";
import { ArrowUpRight } from "lucide-react";

interface LandingNavProps {
  onRequestAccess: () => void;
}

export function LandingNav({ onRequestAccess }: LandingNavProps) {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-white/[0.08] bg-[#0B0D13]/60 backdrop-blur-2xl transition-all duration-300">
      <div className="mx-auto flex max-w-[1400px] items-center justify-between px-4 py-3.5 sm:px-6 lg:px-8">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-3 group">
          <div className="relative flex h-9 w-9 items-center justify-center rounded-xl border border-[#38BDF8]/40 bg-white/[0.04] p-2 shadow-[0_0_20px_rgba(56,189,248,0.25)] backdrop-blur-xl transition-all duration-300 group-hover:border-[#38BDF8]/70 group-hover:shadow-[0_0_25px_rgba(56,189,248,0.5)] group-hover:bg-white/[0.08]">
            <svg viewBox="0 0 24 24" fill="none" className="h-full w-full text-[#38BDF8] animate-spin-slow">
              <path
                d="M12 3a9 9 0 0 1 9 9c0 3.5-2 6.5-5 8-1.5.75-2.5 0-2.5-1.5 0-1.5 1-2.5 2-3.5 1.5-1.5 2-2.5 2-3a5.5 5.5 0 0 0-9.5-3.8"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              />
              <path
                d="M12 21a9 9 0 0 1-9-9c0-3.5 2-6.5 5-8 1.5-.75 2.5 0 2.5 1.5 0 1.5-1 2.5-2 3.5-1.5 1.5-2 2.5-2 3a5.5 5.5 0 0 0 9.5 3.8"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              />
              <circle cx="12" cy="12" r="2" fill="currentColor" />
            </svg>
          </div>
          <span className="font-display text-sm font-bold tracking-[0.22em] text-white">
            CYCLOVISION
          </span>
        </Link>

        {/* Right CTA Actions */}
        <div className="flex items-center gap-3">
          <Link
            to="/login"
            className="rounded-lg border border-white/[0.08] bg-white/[0.03] px-3.5 py-2 text-[13px] font-medium tracking-wide text-[#94A3B8] backdrop-blur-xl transition-all hover:border-[#38BDF8]/40 hover:bg-white/[0.08] hover:text-white"
          >
            Sign In
          </Link>
          <Link
            to="/dashboard"
            className="rounded-lg border border-white/[0.08] bg-white/[0.03] px-3.5 py-2 text-[13px] font-medium tracking-wide text-[#94A3B8] backdrop-blur-xl transition-all hover:border-[#38BDF8]/40 hover:bg-white/[0.08] hover:text-white"
          >
            Console
          </Link>
          <button
            onClick={onRequestAccess}
            className="group relative inline-flex items-center gap-1.5 overflow-hidden rounded-lg bg-gradient-to-r from-[#0284C7] via-[#38BDF8] to-[#60A5FA] px-4 py-2 text-[13px] font-semibold text-[#090D14] shadow-[0_0_25px_rgba(56,189,248,0.4)] transition-all duration-300 hover:shadow-[0_0_35px_rgba(56,189,248,0.7)] hover:brightness-110 active:scale-[0.98]"
          >
            <span>Request Access</span>
            <ArrowUpRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
          </button>
        </div>
      </div>
    </header>
  );
}
