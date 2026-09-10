import { useState } from "react";
import { Link, useNavigate } from "@tanstack/react-router";
import { Mail, Lock, User, Eye, EyeOff, ArrowRight, ArrowLeft, ShieldCheck } from "lucide-react";

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
      setSubmittedMessage(mode === "login" ? "Signed in successfully. Redirecting..." : "Account created. Redirecting...");
      setTimeout(() => {
        navigate({ to: "/dashboard" });
      }, 600);
    }, 500);
  };

  return (
    <div className="relative min-h-screen bg-[#07090E] text-[#F8FAFC] selection:bg-[#38BDF8] selection:text-[#090D14] overflow-x-hidden font-sans flex flex-col justify-between">
      {/* 1. Subtle Planetary Atmosphere Background Glows */}
      <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden transform-gpu">
        <div className="absolute -top-[20%] left-1/2 -translate-x-1/2 h-[750px] w-[1200px] rounded-full bg-gradient-to-b from-[#38BDF8]/14 via-[#0284C7]/8 to-transparent blur-[180px]" />
        <div className="absolute top-[30%] -right-[15%] h-[600px] w-[600px] rounded-full bg-[#1D4ED8]/10 blur-[200px]" />
        <div className="absolute bottom-0 -left-[15%] h-[600px] w-[600px] rounded-full bg-[#06B6D4]/8 blur-[200px]" />
        <div className="absolute inset-0 bg-[radial-gradient(#38BDF8_1px,transparent_1px)] [background-size:64px_64px] opacity-[0.05] [mask-image:radial-gradient(ellipse_70%_70%_at_50%_50%,#000_60%,transparent_100%)]" />
      </div>

      {/* 2. Top Navigation Bar */}
      <header className="sticky top-0 z-50 w-full border-b border-white/[0.08] bg-[#0B0D13]/70 backdrop-blur-2xl transition-all duration-300">
        <div className="mx-auto flex max-w-[1400px] items-center justify-between px-4 py-3.5 sm:px-6 lg:px-8">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="relative flex h-9 w-9 items-center justify-center rounded-xl border border-[#38BDF8]/40 bg-white/[0.04] p-2 shadow-[0_0_20px_rgba(56,189,248,0.2)] backdrop-blur-xl transition-all duration-300 group-hover:border-[#38BDF8]/70 group-hover:bg-white/[0.08]">
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
            <span className="font-display text-sm font-bold tracking-[0.22em] text-white">
              CYCLOVISION
            </span>
          </Link>

          {/* Right Actions */}
          <div className="flex items-center gap-3">
            <Link
              to="/dashboard"
              className="rounded-lg border border-white/[0.08] bg-white/[0.03] px-3.5 py-2 text-[13px] font-medium tracking-wide text-[#94A3B8] backdrop-blur-xl transition-all hover:border-[#38BDF8]/40 hover:bg-white/[0.08] hover:text-white"
            >
              Console
            </Link>
            <Link
              to="/"
              className="group relative inline-flex items-center gap-1.5 overflow-hidden rounded-lg bg-gradient-to-r from-[#0284C7] via-[#38BDF8] to-[#60A5FA] px-4 py-2 text-[13px] font-semibold text-[#090D14] shadow-[0_0_20px_rgba(56,189,248,0.35)] transition-all duration-300 hover:shadow-[0_0_30px_rgba(56,189,248,0.6)] hover:brightness-110 active:scale-[0.98]"
            >
              <ArrowLeft className="h-4 w-4 transition-transform group-hover:-translate-x-0.5" />
              <span>Back to home</span>
            </Link>
          </div>
        </div>
      </header>

      {/* 3. Main Center Authentication Card */}
      <main className="relative z-10 flex flex-1 items-center justify-center px-4 py-12 sm:px-6">
        <div className="w-full max-w-[440px] rounded-3xl border border-white/[0.10] bg-[#0C101A]/90 p-8 sm:p-9 shadow-[0_25px_70px_rgba(0,0,0,0.75),inset_0_1px_1px_rgba(255,255,255,0.12)] backdrop-blur-2xl transition-all duration-300">
          {/* Header */}
          <div className="text-center mb-7">
            <h1 className="font-display text-2xl font-bold tracking-tight text-white sm:text-3xl">
              {mode === "login" ? "Welcome back" : "Create your account"}
            </h1>
            <p className="mt-2 text-xs text-[#94A3B8] sm:text-sm">
              {mode === "login"
                ? "Sign in to continue to your CycloVision workspace."
                : "Start exploring your CycloVision workspace."}
            </p>
          </div>

          {submittedMessage ? (
            <div className="py-8 text-center animate-fade-in">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 shadow-md">
                <ShieldCheck className="h-6 w-6" />
              </div>
              <p className="mt-4 text-sm font-medium text-white">{submittedMessage}</p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Full Name for Signup */}
              {mode === "signup" && (
                <div className="space-y-1.5 animate-fade-in">
                  <label className="block text-[11px] font-medium tracking-wider text-[#94A3B8] uppercase">
                    Full name
                  </label>
                  <div className="relative">
                    <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-[#64748B]">
                      <User className="h-4 w-4" />
                    </div>
                    <input
                      type="text"
                      required
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="Enter your full name"
                      style={{ colorScheme: "dark" }}
                      className="w-full rounded-xl border border-white/[0.08] bg-[#161F33]/60 py-2.5 pl-10 pr-3.5 text-xs text-white placeholder-[#475569] transition-all focus:border-[#38BDF8]/60 focus:bg-[#1A253D] focus:outline-none focus:ring-1 focus:ring-[#38BDF8]/30 [&:-webkit-autofill]:[box-shadow:0_0_0_1000px_#0e1526_inset] [&:-webkit-autofill]:[-webkit-text-fill-color:#fff]"
                    />
                  </div>
                </div>
              )}

              {/* Email Address */}
              <div className="space-y-1.5">
                <label className="block text-[11px] font-medium tracking-wider text-[#94A3B8] uppercase">
                  Email address
                </label>
                <div className="relative">
                  <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-[#64748B]">
                    <Mail className="h-4 w-4" />
                  </div>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@company.com"
                    style={{ colorScheme: "dark" }}
                    className="w-full rounded-xl border border-white/[0.08] bg-[#161F33]/60 py-2.5 pl-10 pr-3.5 text-xs text-white placeholder-[#475569] transition-all focus:border-[#38BDF8]/60 focus:bg-[#1A253D] focus:outline-none focus:ring-1 focus:ring-[#38BDF8]/30 [&:-webkit-autofill]:[box-shadow:0_0_0_1000px_#0e1526_inset] [&:-webkit-autofill]:[-webkit-text-fill-color:#fff]"
                  />
                </div>
              </div>

              {/* Password */}
              <div className="space-y-1.5">
                <label className="block text-[11px] font-medium tracking-wider text-[#94A3B8] uppercase">
                  Password
                </label>
                <div className="relative">
                  <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-[#64748B]">
                    <Lock className="h-4 w-4" />
                  </div>
                  <input
                    type={showPassword ? "text" : "password"}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder={mode === "login" ? "Enter your password" : "Create a password"}
                    style={{ colorScheme: "dark" }}
                    className="w-full rounded-xl border border-white/[0.08] bg-[#161F33]/60 py-2.5 pl-10 pr-10 text-xs text-white placeholder-[#475569] transition-all focus:border-[#38BDF8]/60 focus:bg-[#1A253D] focus:outline-none focus:ring-1 focus:ring-[#38BDF8]/30 [&:-webkit-autofill]:[box-shadow:0_0_0_1000px_#0e1526_inset] [&:-webkit-autofill]:[-webkit-text-fill-color:#fff]"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 flex items-center pr-3.5 text-[#64748B] hover:text-[#94A3B8] transition-colors"
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              {/* Confirm Password for Signup */}
              {mode === "signup" && (
                <div className="space-y-1.5 animate-fade-in">
                  <label className="block text-[11px] font-medium tracking-wider text-[#94A3B8] uppercase">
                    Confirm password
                  </label>
                  <div className="relative">
                    <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-[#64748B]">
                      <Lock className="h-4 w-4" />
                    </div>
                    <input
                      type={showConfirmPassword ? "text" : "password"}
                      required
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      placeholder="Re-enter your password"
                      style={{ colorScheme: "dark" }}
                      className="w-full rounded-xl border border-white/[0.08] bg-[#161F33]/60 py-2.5 pl-10 pr-10 text-xs text-white placeholder-[#475569] transition-all focus:border-[#38BDF8]/60 focus:bg-[#1A253D] focus:outline-none focus:ring-1 focus:ring-[#38BDF8]/30 [&:-webkit-autofill]:[box-shadow:0_0_0_1000px_#0e1526_inset] [&:-webkit-autofill]:[-webkit-text-fill-color:#fff]"
                    />
                    <button
                      type="button"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      className="absolute inset-y-0 right-0 flex items-center pr-3.5 text-[#64748B] hover:text-[#94A3B8] transition-colors"
                    >
                      {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                </div>
              )}

              {/* Remember & Forgot Password (Login Only) */}
              {mode === "login" && (
                <div className="flex items-center justify-between text-xs pt-1">
                  <label className="flex items-center gap-2 text-[#94A3B8] hover:text-white cursor-pointer select-none">
                    <input
                      type="checkbox"
                      checked={rememberMe}
                      onChange={(e) => setRememberMe(e.target.checked)}
                      className="h-3.5 w-3.5 rounded border-white/20 bg-[#161F33] text-[#38BDF8] focus:ring-[#38BDF8]/40"
                    />
                    <span className="text-[11px]">Remember me</span>
                  </label>
                  <a
                    href="#"
                    onClick={(e) => {
                      e.preventDefault();
                      alert("Password reset instructions sent to your registered email.");
                    }}
                    className="text-[11px] text-[#38BDF8] hover:text-[#7DD3FC] transition-colors hover:underline underline-offset-4"
                  >
                    Forgot password?
                  </a>
                </div>
              )}

              {/* Action Button */}
              <button
                type="submit"
                disabled={loading}
                className="group relative mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-[#22D3EE] via-[#06B6D4] to-[#0284C7] py-3 text-xs font-bold text-[#050B14] shadow-[0_0_25px_rgba(34,211,238,0.4)] transition-all duration-300 hover:shadow-[0_0_35px_rgba(34,211,238,0.65)] hover:brightness-110 active:scale-[0.98] disabled:opacity-60"
              >
                <span>{loading ? "Processing..." : mode === "login" ? "Log in" : "Create Account"}</span>
                {!loading && <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />}
              </button>

              {/* Mode Switcher */}
              <div className="mt-5 text-center text-xs text-[#94A3B8] pt-1">
                {mode === "login" ? (
                  <span>
                    New to CycloVision?{" "}
                    <button
                      type="button"
                      onClick={() => setMode("signup")}
                      className="font-medium text-[#38BDF8] hover:text-[#7DD3FC] transition-colors underline-offset-4 hover:underline ml-1"
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
                      className="font-medium text-[#38BDF8] hover:text-[#7DD3FC] transition-colors underline-offset-4 hover:underline ml-1"
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

      {/* Bottom spacing */}
      <div className="h-6" />
    </div>
  );
}
