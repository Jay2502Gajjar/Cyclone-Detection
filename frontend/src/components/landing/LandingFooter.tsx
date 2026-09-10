import { Link } from "@tanstack/react-router";

export function LandingFooter() {
  const columns = [
    {
      title: "DATA FEEDS",
      links: [
        { label: "Global Tropics", to: "/map" },
        { label: "JTWC Clusters", to: "/dashboard" },
        { label: "Model Sandbox", to: "/ai" },
        { label: "Operational Feeds", to: "/dashboard" },
      ],
    },
    {
      title: "DEVELOPER ACCESS",
      links: [
        { label: "gRPC Spec", to: "/ai" },
        { label: "Python SDK", to: "/ai" },
        { label: "GeoJSON Schemas", to: "/map" },
        { label: "Mission Webhooks", to: "/alerts" },
      ],
    },
    {
      title: "RESEARCH & DATA",
      links: [
        { label: "Forecaster Whitepaper", to: "/historical" },
        { label: "ONNX Model (2025)", to: "/ai" },
        { label: "Global Bathymetry", to: "/map" },
        { label: "Rapid Intensification", to: "/predictions" },
      ],
    },
    {
      title: "GOVERNANCE",
      links: [
        { label: "Export Controls", to: "#" },
        { label: "ITAR Compliance", to: "#" },
        { label: "Data Policy", to: "#" },
        { label: "SLAs & Availability", to: "#" },
      ],
    },
  ];

  return (
    <footer className="relative border-t border-white/[0.08] bg-[#07080C]/80 py-16 backdrop-blur-2xl">
      <div className="mx-auto max-w-[1400px] px-4 sm:px-6 lg:px-8">
        <div className="grid gap-10 md:grid-cols-2 lg:grid-cols-6">
          {/* Logo & Bio column */}
          <div className="lg:col-span-2">
            <Link to="/" className="flex items-center gap-3 group">
              <div className="flex h-8 w-8 items-center justify-center rounded-xl border border-[#38BDF8]/40 bg-white/[0.04] p-1.5 shadow-[0_0_15px_rgba(56,189,248,0.2)] backdrop-blur-xl">
                <svg viewBox="0 0 24 24" fill="none" className="h-full w-full text-[#38BDF8]">
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
              <span className="font-display text-sm font-bold tracking-[0.24em] text-white">
                V<span className="text-[#38BDF8]">AI</span>YU
              </span>
            </Link>

            <p className="mt-4 max-w-sm text-xs leading-relaxed text-[#94A3B8]">
              Sub-kilometer planetary meteorological intelligence. Continuous neural tensor prediction for high-stakes storm defense and operations.
            </p>
          </div>

          {/* Nav Columns */}
          {columns.map((col) => (
            <div key={col.title}>
              <h4 className="font-display text-[11px] font-bold tracking-[0.18em] text-white uppercase">
                {col.title}
              </h4>
              <ul className="mt-4 space-y-2.5 text-xs text-[#94A3B8]">
                {col.links.map((link) => (
                  <li key={link.label}>
                    {link.to.startsWith("#") ? (
                      <a href={link.to} className="transition-colors hover:text-white">
                        {link.label}
                      </a>
                    ) : (
                      <Link to={link.to} className="transition-colors hover:text-white">
                        {link.label}
                      </Link>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Bottom Legal & Compliance Strip */}
        <div className="mt-14 flex flex-wrap items-center justify-between gap-4 border-t border-white/[0.06] pt-8 text-[11px] text-[#94A3B8]">
          <div>
            © 2026 VAIYU Inc. All rights reserved. Sub-kilometer neural simulation is active in all operational conditions.
          </div>
          <div className="flex items-center gap-4">
            <span className="text-[#38BDF8] font-medium">ITAR Compliant</span>
            <span>•</span>
            <a href="#" className="hover:text-white transition-colors">Terms of Use</a>
          </div>
        </div>
      </div>
    </footer>
  );
}
