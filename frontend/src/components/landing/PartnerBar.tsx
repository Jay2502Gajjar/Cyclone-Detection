import { Shield, Radio, Activity, Globe, Wind } from "lucide-react";
import { ScrollReveal } from "./ScrollReveal";

export function PartnerBar() {
  const partners = [
    { name: "NOAA NESDIS", icon: Globe, region: "US Ocean & Atmosphere" },
    { name: "ECMWF", icon: Activity, region: "European Centre" },
    { name: "JTWC", icon: Shield, region: "Joint Typhoon Warning" },
    { name: "JMA TOKYO", icon: Radio, region: "Japan Meteorological" },
    { name: "BOM AUSTRALIA", icon: Wind, region: "Bureau of Meteorology" },
  ];

  return (
    <section id="organizations" className="relative py-10">
      <div className="mx-auto max-w-[1400px] px-4 sm:px-6 lg:px-8">
        <ScrollReveal direction="fade" delay={50}>
          <p className="text-center font-display text-[11px] font-semibold tracking-[0.24em] text-[#94A3B8]/90 uppercase">
            PARTNERING METEOROLOGICAL & DEFENSE OPERATIONS GLOBALLY
          </p>
        </ScrollReveal>

        <div className="mt-8 flex flex-wrap items-center justify-center gap-5 sm:gap-6 md:gap-8 lg:gap-10">
          {partners.map((partner, idx) => {
            const Icon = partner.icon;
            return (
              <ScrollReveal
                key={partner.name}
                direction="up"
                delay={80 + idx * 70}
                distance={16}
              >
                <div className="group flex items-center gap-3 rounded-full border border-white/[0.08] bg-white/[0.03] px-5 py-2.5 shadow-[0_4px_20px_0_rgba(0,0,0,0.2),inset_0_1px_1px_rgba(255,255,255,0.08)] backdrop-blur-xl transition-all duration-300 hover:border-[#38BDF8]/50 hover:bg-white/[0.07] hover:shadow-[0_0_20px_rgba(56,189,248,0.25)] hover:-translate-y-0.5">
                  <div className="flex h-5 w-5 items-center justify-center rounded-full bg-[#38BDF8]/10 text-[#38BDF8] transition-transform group-hover:scale-110">
                    <Icon className="h-3.5 w-3.5" />
                  </div>
                  <span className="font-display text-[12px] font-semibold tracking-wider text-[#F8FAFC]">
                    {partner.name}
                  </span>
                </div>
              </ScrollReveal>
            );
          })}
        </div>
      </div>
    </section>
  );
}
