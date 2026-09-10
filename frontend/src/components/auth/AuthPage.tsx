import { useState } from "react";
import { Link, useNavigate } from "@tanstack/react-router";
import { Mail, Lock, User, Eye, EyeOff, ShieldCheck, ArrowRight, ArrowLeft, ArrowUpRight } from "lucide-react";

export function AuthPage() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);

  // Form State
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [submittedMessage, setSubmittedMessage] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    setTimeout(() => {
      setLoading(false);
      setSubmittedMessage(mode === "login" ? "Operator authenticated! Initializing mission console..." : "Account created! Routing security credentials...");
      setTimeout(() => {
        navigate({ to: "/dashboard" });
      }, 750);
    }, 600);
  };

  return (
    <div className="relative min-h-screen bg-[#06080D] text-[#F8FAFC] selection:bg-[#38BDF8] selection:text-[#090D14] overflow-x-hidden font-sans flex flex-col justify-between">
      {/* 1. Expansive, Wide-Spread Planetary Light Fields & Nebulae (Identical to Landing Page) */}
      <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden transform-gpu">
        {/* Top Center Sky Cyan Flare */}
        <div className="absolute -top-[25%] left-1/2 -translate-x-1/2 h-[900px] w-[1400px] rounded-full bg-gradient-to-b from-[#38BDF8]/20 via-[#0284C7]/14 to-transparent blur-[220px] transform-gpu" />

        {/* Top-Right Cybernetic Cobalt Aurora */}
        <div className="absolute top-[8%] -right-[18%] h-[900px] w-[900px] rounded-full bg-gradient-to-br from-[#1E40AF]/18 via-[#1D4ED8]/12 to-transparent blur-[240px] transform-gpu" />

        {/* Mid-Left Deep Pacific Indigo Nebula */}
        <div className="absolute top-[35%] -left-[18%] h-[1000px] w-[1000px] rounded-full bg-gradient-to-tr from-[#1E3A8A]/22 via-[#1E40AF]/15 to-transparent blur-[260px] transform-gpu" />

        {/* Mid-Right Luminous Turquoise Cyclone Bloom */}
        <div className="absolute top-[55%] -right-[20%] h-[1000px] w-[1000px] rounded-full bg-gradient-to-tl from-[#06B6D4]/18 via-[#0284C7]/15 to-transparent blur-[250px] transform-gpu" />

        {/* Cosmic Micro-Dust & Starfield Accents */}
        <div className="absolute inset-0 bg-[radial-gradient(#38BDF8_1px,transparent_1px)] [background-size:64px_64px] opacity-[0.07] [mask-image:radial-gradient(ellipse_70%_70%_at_50%_50%,#000_60%,transparent_100%)]" />

        {/* Orbital Wireframe Decorative Geometry */}
        <div className="absolute top-20 right-20 h-[380px] w-[380px] rounded-full border border-white/[0.04] hidden lg:block" />
        <div className="absolute bottom-20 left-20 h-[440px] w-[440px] rounded-full border border-cyan-400/[0.03] hidden lg:block" />
      </div>

      {/* 2. Top Navigation Bar (Consistent with Landing Page Header) */}
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

          {/* Right Action Links */}
          <div className="flex items-center gap-4">
            <Link
              to="/dashboard"
              className="rounded-lg border border-white/[0.08] bg-white/[0.03] px-3.5 py-2 text-[13px] font-medium tracking-wide text-[#94A3B8] backdrop-blur-xl transition-all hover:border-[#38BDF8]/40 hover:bg-white/[0.08] hover:text-white"
            >
              Console
            </Link>
            <Link
              to="/"
              className="group relative inline-flex items-center gap-1.5 rounded-lg border border-white/[0.12] bg-white/[0.04] px-4 py-2 text-[13px] font-semibold text-white shadow-[0_8px_32px_0_rgba(0,0,0,0.37),inset_0_1px_1px_rgba(255,255,255,0.12)] backdrop-blur-2xl transition-all duration-300 hover:border-[#38BDF8]/40 hover:bg-white/[0.08] hover:shadow-[0_0_20px_rgba(56,189,248,0.2)] active:scale-[0.98]"
            >
              <ArrowLeft className="h-4 w-4 text-[#94A3B8] transition-transform group-hover:-translate-x-0.5 group-hover:text-[#38BDF8]" />
              <span>Back to home</span>
            </Link>
          </div>
        </div>
      </header>

      {/* 3. Main Glassmorphic Auth Centerpiece */}
      <main className="relative z-10 flex flex-1 items-center justify-center px-4 py-12 sm:px-6">
        <div className="w-full max-w-[460px] rounded-3xl border border-white/[0.12] bg-[#0E1118]/85 p-8 sm:p-10 shadow-[0_25px_80px_rgba(0,0,0,0.85),inset_0_1px_1px_rgba(255,255,255,0.15)] backdrop-blur-2xl transition-all duration-300">
          {/* Frosted Glass Core Badge */}
          <div className="flex justify-center mb-6">
            <div className="inline-flex items-center gap-2.5 rounded-full border border-white/[0.12] bg-white/[0.04] px-4 py-1.5 text-[11px] font-semibold tracking-wider text-[#38BDF8] uppercase shadow-[0_8px_32px_0_rgba(0,0,0,0.37),inset_0_1px_1px_rgba(255,255,255,0.15)] backdrop-blur-2xl transition-all duration-300 hover:border-[#38BDF8]/50 hover:shadow-[0_0_20px_rgba(56,189,248,0.25)]">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[#38BDF8] opacity-75" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-[#38BDF8]" />
              </span>
              <span className="tracking-[0.2em]">{mode === "login" ? "SECURE OPERATOR ACCESS" : "SECURE REGISTRATION"}</span>
            </div>
          </div>

          {/* Heading */}
          <div className="text-center mb-7">
            <h1 className="font-display text-3xl font-extrabold tracking-tight text-white sm:text-[32px]">
              {mode === "login" ? "Welcome back" : "Create your account"}
            </h1>
            <p className="mt-2 text-xs leading-relaxed text-[#94A3B8] sm:text-sm">
              {mode === "login"
                ? "Sign in to access your continuous satellite AI workspace."
                : "Join the neural cyclone intelligence & telemetry network."}
            </p>
          </div>

          {submittedMessage ? (
            <div className="py-8 text-center animate-fade-in">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-[#10B981]/15 text-[#10B981] border border-[#10B981]/30 shadow-[0_0_25px_rgba(16,185,129,0.35)]">
                <ShieldCheck className="h-7 w-7" />
              </div>
              <p className="mt-5 font-display text-lg font-bold text-white">{submittedMessage}</p>
              <p className="mt-2 text-xs text-[#94A3B8]">Routing telemetry session to mission control...</p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Full Name for Signup */}
              {mode === "signup" && (
                <div className="space-y-1.5 animate-fade-in">
                  <label className="block text-[11px] font-semibold tracking-wider text-[#94A3B8] uppercase">
                    Full name
                  </label>
                  <div className="relative">
                    <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-[#94A3B8]">
                      <User className="h-4 w-4" />
                    </div>
                    <input
                      type="text"
                      required
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="Dr. Sarah Jenkins"
                      style={{ colorScheme: "dark" }}
                      className="w-full rounded-xl border border-white/[0.12] bg-white/[0.04] py-3 pl-10 pr-4 text-xs text-white placeholder-[#64748B] backdrop-blur-xl transition-all focus:border-[#38BDF8]/60 focus:bg-white/[0.08] focus:outline-none focus:ring-1 focus:ring-[#38BDF8]/40 [&:-webkit-autofill]:[box-shadow:0_0_0_1000px_#0e1526_inset] [&:-webkit-autofill]:[-webkit-text-fill-color:#fff]"
                    />
                  </div>
                </div>
              )}

              {/* Email Address */}
              <div className="space-y-1.5">
                <label className="block text-[11px] font-semibold tracking-wider text-[#94A3B8] uppercase">
                  Email address
                </label>
                <div className="relative">
                  <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-[#94A3B8]">
                    <Mail className="h-4 w-4" />
                  </div>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="forecaster@cyclovision.ai"
                    style={{ colorScheme: "dark" }}
                    className="w-full rounded-xl border border-white/[0.12] bg-white/[0.04] py-3 pl-10 pr-4 text-xs text-white placeholder-[#64748B] backdrop-blur-xl transition-all focus:border-[#38BDF8]/60 focus:bg-white/[0.08] focus:outline-none focus:ring-1 focus:ring-[#38BDF8]/40 [&:-webkit-autofill]:[box-shadow:0_0_0_1000px_#0e1526_inset] [&:-webkit-autofill]:[-webkit-text-fill-color:#fff]"
                  />
                </div>
              </div>

              {/* Password */}
              <div className="space-y-1.5">
                <label className="block text-[11px] font-semibold tracking-wider text-[#94A3B8] uppercase">
                  Password
                </label>
                <div className="relative">
                  <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-[#94A3B8]">
                    <Lock className="h-4 w-4" />
                  </div>
                  <input
                    type={showPassword ? "text" : "password"}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder={mode === "login" ? "Enter your security password" : "Create strong password"}
                    style={{ colorScheme: "dark" }}
                    className="w-full rounded-xl border border-white/[0.12] bg-white/[0.04] py-3 pl-10 pr-10 text-xs text-white placeholder-[#64748B] backdrop-blur-xl transition-all focus:border-[#38BDF8]/60 focus:bg-white/[0.08] focus:outline-none focus:ring-1 focus:ring-[#38BDF8]/40 [&:-webkit-autofill]:[box-shadow:0_0_0_1000px_#0e1526_inset] [&:-webkit-autofill]:[-webkit-text-fill-color:#fff]"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 flex items-center pr-3.5 text-[#94A3B8] hover:text-white transition-colors"
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              {/* Confirm Password for Signup */}
              {mode === "signup" && (
                <div className="space-y-1.5 animate-fade-in">
                  <label className="block text-[11px] font-semibold tracking-wider text-[#94A3B8] uppercase">
                    Confirm password
                  </label>
                  <div className="relative">
                    <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-[#94A3B8]">
                      <Lock className="h-4 w-4" />
                    </div>
                    <input
                      type={showConfirmPassword ? "text" : "password"}
                      required
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="Confirm security password"
                      style={{ colorScheme: "dark" }}
                      className="w-full rounded-xl border border-white/[0.12] bg-white/[0.04] py-3 pl-10 pr-10 text-xs text-white placeholder-[#64748B] backdrop-blur-xl transition-all focus:border-[#38BDF8]/60 focus:bg-white/[0.08] focus:outline-none focus:ring-1 focus:ring-[#38BDF8]/40 [&:-webkit-autofill]:[box-shadow:0_0_0_1000px_#0e1526_inset] [&:-webkit-autofill]:[-webkit-text-fill-color:#fff]"
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute inset-y-0 right-0 flex items-center pr-3.5 text-[#94A3B8] hover:text-white transition-colors"
                    >
                      {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>
              )}

              {/* Remember Me & Forgot Password */}
              {mode === "login" && (
                <div className="flex items-center justify-between text-xs pt-1">
                  <label className="flex items-center gap-2 text-[#94A3B8] hover:text-white cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={rememberMe}
                      onChange={(e) => setRememberMe(e.target.checked)}
                      className="h-3.5 w-3.5 rounded border-white/20 bg-white/[0.04] text-[#38BDF8] focus:ring-[#38BDF8]/40"
                    />
                    <span>Remember operator</span>
                  </label>
                  <a
                    href="#"
                    onClick={(e) => {
                      e.preventDefault();
                      alert("Password reset instructions have been routed to your registered email.");
                    }}
                    className="text-[#38BDF8] hover:text-[#7DD3FC] transition-colors hover:underline underline-offset-4"
                  >
                    Forgot password?
                  </a>
                </div>
              )}

              {/* Primary Action Button (Identical to Landing Page Main CTA) */}
              <button
                type="submit"
                disabled={loading}
                className="group relative mt-6 flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-[#0284C7] via-[#38BDF8] to-[#60A5FA] px-6 py-3.5 text-sm font-semibold text-[#090D14] shadow-[0_0_30px_rgba(56,189,248,0.45)] transition-all duration-300 hover:shadow-[0_0_45px_rgba(56,189,248,0.7)] hover:brightness-110 active:scale-[0.98] disabled:opacity-70"
              >
                <span>{loading ? "Authenticating..." : mode === "login" ? "Sign In to Workspace" : "Create Account"}</span>
                {!loading && <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />}
              </button>

              {/* Mode Switcher */}
              <div className="mt-6 text-center text-xs text-[#94A3B8] pt-2">
                {mode === "login" ? (
                  <span>
                    New to CycloVision?{" "}
                    <button
                      type="button"
                      onClick={() => setMode("signup")}
                      className="font-semibold text-[#38BDF8] hover:text-[#7DD3FC] transition-colors underline-offset-4 hover:underline ml-1"
                    >
                      Create an account
                    </button>
                  </span>
                ) : (
                  <span>
                    Already have an account?{" "}
                    <button
                      type="button"
                      onClick={() => setMode("login")}
                      className="font-semibold text-[#38BDF8] hover:text-[#7DD3FC] transition-colors underline-offset-4 hover:underline ml-1"
                    >
                      Sign in
                    </button>
                  </span>
                )}
              </div>
            </form>
          )}
        </div>
      </main>

      {/* 4. Bottom Footer (Matching Landing Page Footer Style) */}
      <footer className="relative z-20 w-full border-t border-white/[0.08] bg-[#07080C]/80 py-6 backdrop-blur-2xl text-center text-[12px] text-[#94A3B8]">
        <div className="mx-auto flex max-w-[1400px] flex-col items-center justify-between gap-3 px-4 sm:flex-row sm:px-6 lg:px-8">
          <p>© 2026 CycloVision Neural Research. Continuous Satellite AI Systems.</p>
          <div className="flex items-center gap-6">
            <span className="text-white/60">Protected by 256-bit TLS · SOC2 Certified</span>
            <Link to="/" className="text-[#38BDF8] hover:underline">Privacy & Security</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
