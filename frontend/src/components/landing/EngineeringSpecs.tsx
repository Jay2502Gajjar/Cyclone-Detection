import { Cpu, Satellite, Waves } from "lucide-react";
import { ScrollReveal } from "./ScrollReveal";

export function EngineeringSpecs() {
  const specs = [
    {
      num: "01",
      tag: "REAL-TIME ASSIMILATION",
      title: "Radiometric Satellite Vision",
      desc: "Direct assimilation from 14 geostationary satellite streams including GOES-R/S, Himawari-8/9, and INSAT-3D. Sub-second convolutional spectral segmentation identifies convection and eyewall replacement cycles.",
      statLabel: "REFRESH CADENCE",
      statValue: "30s Real-Time",
      icon: Satellite,
    },
    {
      num: "02",
      tag: "PHYSICS INTEGRATION",
      title: "Physics-Informed Ensembles",
      desc: "Loss functions are strictly constrained by atmospheric baroclinicity and boundary-layer kinetic energy conservation. Eliminates chaotic numerical drift in tropical trajectories.",
      statLabel: "ENSEMBLE RUNS",
      statValue: ">10,000 PER HOUR",
      icon: Cpu,
    },
    {
      num: "03",
      tag: "SURGE MODELING",
      title: "Coastal Surge Hydrodynamics",
      desc: "Direct coupling of wind-stress fields with high-resolution GEBCO bathymetric data. Predicts localized coastal storm surges down to 100m intervals across 250,000km of coastline.",
      statLabel: "SURGE ACCURACY",
      statValue: "<0.4m Mean Delta",
      icon: Waves,
    },
  ];

  return (
    <section id="product" className="relative py-20 md:py-28">
      <div className="mx-auto max-w-[1400px] px-4 sm:px-6 lg:px-8">
        {/* Section Heading */}
        <div className="text-center">
          <ScrollReveal direction="down" delay={50} distance={16}>
            <div className="inline-flex items-center gap-2 rounded-full border border-white/[0.12] bg-white/[0.04] px-4 py-1.5 text-[11px] font-semibold tracking-wider text-[#38BDF8] uppercase shadow-[0_8px_32px_0_rgba(0,0,0,0.37),inset_0_1px_1px_rgba(255,255,255,0.1)] backdrop-blur-2xl">
              <Cpu className="h-3.5 w-3.5" />
              <span className="tracking-[0.2em]">ENGINEERING SPECIFICATIONS</span>
            </div>
          </ScrollReveal>

          <ScrollReveal direction="up" delay={120} distance={20}>
            <h2 className="mt-5 font-display text-3xl font-extrabold tracking-tight text-white sm:text-4xl md:text-5xl">
              Physics-informed deep learning at planetary scale
            </h2>
          </ScrollReveal>

          <ScrollReveal direction="up" delay={180} distance={18}>
            <p className="mx-auto mt-4 max-w-3xl text-sm leading-relaxed text-[#94A3B8] sm:text-base">
              Traditional numerical weather models require 4 to 6 hours per forecast cycle. VAIYU assimilates multi-spectral satellite telemetry, delivering sub-kilometer resolution 10-day forecasts in 42 seconds.
            </p>
          </ScrollReveal>
        </div>

        {/* 3 Staggered Frosted Engineering Cards */}
        <div className="mt-14 grid gap-6 md:grid-cols-3">
          {specs.map((item, idx) => {
            const Icon = item.icon;
            return (
              <ScrollReveal
                key={item.num}
                direction="up"
                delay={100 + idx * 120}
                distance={32}
                duration={750}
              >
                <div className="group relative flex flex-col justify-between h-full rounded-3xl border border-white/[0.08] bg-white/[0.025] p-6 sm:p-8 shadow-[0_20px_50px_rgba(0,0,0,0.5),inset_0_1px_1px_rgba(255,255,255,0.1)] backdrop-blur-2xl transition-all duration-500 hover:-translate-y-1.5 hover:border-[#38BDF8]/40 hover:bg-white/[0.05] hover:shadow-[0_0_35px_rgba(56,189,248,0.2)]">
                  {/* Subtle Refraction Glow */}
                  <div className="pointer-events-none absolute inset-0 rounded-3xl bg-gradient-to-b from-[#38BDF8]/5 to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100" />

                  <div>
                    {/* Top Bar: Tag & Number */}
                    <div className="flex items-center justify-between">
                      <span className="font-display text-[10px] font-bold tracking-[0.2em] text-[#38BDF8] uppercase">
                        {item.tag}
                      </span>
                      <span className="font-mono text-xs font-semibold text-[#94A3B8]">
                        {item.num}
                      </span>
                    </div>

                    {/* Title & Icon */}
                    <div className="mt-6 flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/[0.1] bg-white/[0.04] text-[#38BDF8] shadow-[inset_0_1px_1px_rgba(255,255,255,0.1)] backdrop-blur-md transition-transform duration-300 group-hover:scale-110">
                        <Icon className="h-5 w-5" />
                      </div>
                      <h3 className="font-display text-lg font-bold tracking-tight text-white">
                        {item.title}
                      </h3>
                    </div>

                    {/* Description */}
                    <p className="mt-4 text-xs leading-relaxed text-[#94A3B8] sm:text-sm">
                      {item.desc}
                    </p>
                  </div>

                  {/* Bottom Metric Strip */}
                  <div className="mt-8 border-t border-white/[0.06] pt-5">
                    <div className="flex items-center justify-between">
                      <span className="font-display text-[10px] font-semibold tracking-wider text-[#94A3B8] uppercase">
                        {item.statLabel}
                      </span>
                      <span className="font-display text-sm font-bold tracking-tight text-[#38BDF8]">
                        {item.statValue}
                      </span>
                    </div>
                  </div>
                </div>
              </ScrollReveal>
            );
          })}
        </div>
      </div>
    </section>
  );
}
