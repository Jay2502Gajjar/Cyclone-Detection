import { useState } from "react";
import { X, Key, Check, ArrowRight, ShieldCheck } from "lucide-react";
import { Link } from "@tanstack/react-router";

interface AccessModalProps {
  isOpen: boolean;
  type: "access" | "specs" | "key" | "specialist";
  onClose: () => void;
}

export function AccessModal({ isOpen, type, onClose }: AccessModalProps) {
  const [email, setEmail] = useState("");
  const [org, setOrg] = useState("");
  const [submitted, setSubmitted] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-xl animate-fade-in">
      <div className="relative w-full max-w-lg rounded-3xl border border-white/[0.15] bg-[#0E1118]/90 p-6 shadow-[0_25px_80px_rgba(0,0,0,0.9),inset_0_1px_1px_rgba(255,255,255,0.15)] backdrop-blur-2xl sm:p-8">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 rounded-xl border border-white/[0.08] p-2 text-[#94A3B8] hover:bg-white/[0.06] hover:text-white transition-colors"
        >
          <X className="h-5 w-5" />
        </button>

        {submitted ? (
          <div className="text-center py-6">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-[#10B981]/15 text-[#10B981] border border-[#10B981]/30 shadow-[0_0_20px_rgba(16,185,129,0.3)]">
              <Check className="h-7 w-7" />
            </div>
            <h3 className="mt-5 font-display text-xl font-bold text-white">
              Access Request Granted
            </h3>
            <p className="mt-2 text-xs text-[#94A3B8]">
              Operational credentials and technical whitepaper have been routed to <span className="text-white font-mono">{email || "your email"}</span>.
            </p>
            <div className="mt-6 flex flex-col gap-2.5">
              <Link
                to="/dashboard"
                onClick={onClose}
                className="w-full inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-[#0284C7] via-[#38BDF8] to-[#60A5FA] py-3 text-xs font-semibold text-[#090D14] shadow-[0_0_20px_rgba(56,189,248,0.4)] hover:brightness-110 transition-all"
              >
                Launch Mission Console Now
                <ArrowRight className="h-4 w-4" />
              </Link>
              <button
                onClick={onClose}
                className="w-full rounded-xl border border-white/[0.08] py-2.5 text-xs font-medium text-[#94A3B8] hover:bg-white/[0.06] hover:text-white transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        ) : (
          <div>
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#38BDF8]/15 text-[#38BDF8] border border-[#38BDF8]/30 shadow-[0_0_15px_rgba(56,189,248,0.25)]">
                <Key className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-display text-lg font-bold text-white">
                  {type === "key"
                    ? "Request Operational API Key"
                    : type === "specs"
                    ? "Read Technical Specifications"
                    : type === "specialist"
                    ? "Consult Meteorology Specialist"
                    : "Request Mission Console Access"}
                </h3>
                <p className="font-display text-[10px] uppercase tracking-wider text-[#38BDF8]">
                  Sub-Kilometer Continuous AI Model V3.2
                </p>
              </div>
            </div>

            <p className="mt-4 text-xs leading-relaxed text-[#94A3B8]">
              Access 30-second inference streams, rapid intensification probability tensors, and high-resolution trajectory meshes.
            </p>

            <form onSubmit={handleSubmit} className="mt-6 space-y-4">
              <div>
                <label className="block font-display text-[10px] font-semibold tracking-wider text-[#94A3B8] uppercase">
                  Work / Agency Email
                </label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="analyst@noaa.gov or defense.ops"
                  className="mt-1.5 w-full rounded-xl border border-white/[0.1] bg-white/[0.03] px-4 py-2.5 text-xs text-white placeholder-[#64748B] backdrop-blur-md focus:border-[#38BDF8] focus:outline-none focus:ring-1 focus:ring-[#38BDF8]"
                />
              </div>

              <div>
                <label className="block font-display text-[10px] font-semibold tracking-wider text-[#94A3B8] uppercase">
                  Organization / Unit
                </label>
                <input
                  type="text"
                  required
                  value={org}
                  onChange={(e) => setOrg(e.target.value)}
                  placeholder="e.g. JTWC, Naval Meteorology, Disaster Mgmt"
                  className="mt-1.5 w-full rounded-xl border border-white/[0.1] bg-white/[0.03] px-4 py-2.5 text-xs text-white placeholder-[#64748B] backdrop-blur-md focus:border-[#38BDF8] focus:outline-none focus:ring-1 focus:ring-[#38BDF8]"
                />
              </div>

              <div className="flex items-center gap-2 text-[11px] text-[#94A3B8]">
                <ShieldCheck className="h-4 w-4 text-[#38BDF8] shrink-0" />
                <span>ITAR & FedRAMP High compliant processing pipeline.</span>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  className="w-full inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-[#0284C7] via-[#38BDF8] to-[#60A5FA] py-3 text-xs font-semibold text-[#090D14] shadow-[0_0_25px_rgba(56,189,248,0.4)] hover:brightness-110 transition-all active:scale-[0.98]"
                >
                  Generate Credentials
                  <ArrowRight className="h-4 w-4" />
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}
