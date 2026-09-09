import { Zap, CheckCircle2 } from "lucide-react";
import { ScrollReveal } from "./ScrollReveal";

export function BenchmarkTable() {
  const rows = [
    {
      metric: "Inference Compute Run Time",
      legacy: "4.2 Hours (512 Cores)",
      blackbox: "15 Seconds (Unconstrained)",
      cyclovision: "42 Seconds (Constrained Phys)",
      isHighlight: false,
    },
    {
      metric: "Convective Core Resolution",
      legacy: "9.0 Kilometers",
      blackbox: "NA (Spatial Blur)",
      cyclovision: "375 Meters (Planetary)",
      isHighlight: true,
    },
    {
      metric: "Rapid Intensification (RI) Precision",
      legacy: "41.2% Success Rate",
      blackbox: "58.4% (Over-fits Calm)",
      cyclovision: "94.8% Accuracy Catch",
      isHighlight: true,
    },
    {
      metric: "Angular Momentum Conservation",
      legacy: "Guaranteed via Numerics",
      blackbox: "Unstable (Velocity Leaks)",
      cyclovision: "Strictly Enforced Loss",
      isHighlight: false,
    },
    {
      metric: "Initial Ingest-to-Alert Time",
      legacy: "180 Minutes",
      blackbox: "45 Minutes",
      cyclovision: "<2 Minutes (Continuous)",
      isHighlight: true,
    },
  ];

  return (
    <section id="hardware" className="relative py-20 md:py-28">
      <div className="mx-auto max-w-[1400px] px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center">
          <ScrollReveal direction="down" delay={50} distance={16}>
            <div className="inline-flex items-center gap-2 rounded-full border border-white/[0.12] bg-white/[0.04] px-4 py-1.5 text-[11px] font-semibold tracking-wider text-[#38BDF8] uppercase shadow-[0_8px_32px_0_rgba(0,0,0,0.37),inset_0_1px_1px_rgba(255,255,255,0.1)] backdrop-blur-2xl">
              <Zap className="h-3.5 w-3.5" />
              <span className="tracking-[0.2em]">BENCHMARK DISRUPTION</span>
            </div>
          </ScrollReveal>

          <ScrollReveal direction="up" delay={120} distance={20}>
            <h2 className="mt-5 font-display text-3xl font-extrabold tracking-tight text-white sm:text-4xl md:text-5xl">
              Outperforming classical frameworks
            </h2>
          </ScrollReveal>

          <ScrollReveal direction="up" delay={180} distance={18}>
            <p className="mx-auto mt-4 max-w-3xl text-sm leading-relaxed text-[#94A3B8] sm:text-base">
              A rigorous comparative evaluation of CycloVision AI against industry-standard numerical simulation (NWP) systems and pure black-box AI emulators.
            </p>
          </ScrollReveal>
        </div>

        {/* Frosted Glass Comparison Table Container */}
        <ScrollReveal direction="up" delay={240} distance={30} duration={800}>
          <div className="mt-14 overflow-x-auto rounded-3xl border border-white/[0.1] bg-white/[0.02] shadow-[0_25px_60px_rgba(0,0,0,0.6),inset_0_1px_1px_rgba(255,255,255,0.12)] backdrop-blur-2xl">
            <table className="w-full min-w-[720px] border-collapse text-left text-sm">
              <thead>
                <tr className="border-b border-white/[0.08] bg-white/[0.03]">
                  <th className="py-5 px-6 font-display text-[11px] font-bold tracking-wider text-[#94A3B8] uppercase">
                    METRIC PROFILE
                  </th>
                  <th className="py-5 px-6 font-display text-[11px] font-bold tracking-wider text-[#94A3B8] uppercase">
                    LEGACY NWP (GFS/ECMWF)
                  </th>
                  <th className="py-5 px-6 font-display text-[11px] font-bold tracking-wider text-[#94A3B8] uppercase">
                    BLACK-BOX AI EMULATOR
                  </th>
                  <th className="relative py-5 px-6 font-display text-[11px] font-bold tracking-wider text-[#38BDF8] uppercase bg-[#38BDF8]/[0.08]">
                    <div className="flex items-center gap-2">
                      <span>CYCLOVISION CORE</span>
                      <span className="rounded-full bg-[#38BDF8] px-2 py-0.5 text-[9px] font-extrabold text-[#090D14] shadow-[0_0_10px_rgba(56,189,248,0.4)]">
                        V3.2
                      </span>
                    </div>
                    {/* Glowing Top Edge */}
                    <div className="absolute top-0 left-0 right-0 h-0.5 bg-[#38BDF8] shadow-[0_0_12px_#38BDF8]" />
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.05]">
                {rows.map((row) => (
                  <tr
                    key={row.metric}
                    className="transition-colors hover:bg-white/[0.04]"
                  >
                    <td className="py-4.5 px-6 font-display font-medium text-white">
                      {row.metric}
                    </td>
                    <td className="py-4.5 px-6 font-mono text-xs text-[#94A3B8]">
                      {row.legacy}
                    </td>
                    <td className="py-4.5 px-6 font-mono text-xs text-[#94A3B8]">
                      {row.blackbox}
                    </td>
                    <td className="py-4.5 px-6 bg-[#38BDF8]/[0.04] font-mono text-xs font-semibold text-[#38BDF8]">
                      <div className="flex items-center gap-2">
                        {row.isHighlight && (
                          <CheckCircle2 className="h-4 w-4 text-[#38BDF8] shrink-0 drop-shadow-[0_0_8px_rgba(56,189,248,0.6)]" />
                        )}
                        <span>{row.cyclovision}</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </ScrollReveal>
      </div>
    </section>
  );
}
