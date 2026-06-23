import React from "react";
import { Link, useLocation } from "react-router-dom";
import { Sparkles } from "lucide-react";

export const Navbar = () => {
  const loc = useLocation();
  const isAdmin = loc.pathname.startsWith("/admin");

  return (
    <header
      data-testid="navbar"
      className="sticky top-0 z-40 bg-[#F9F8F6]/85 backdrop-blur-md border-b-2 border-[#121212]"
    >
      <div className="max-w-7xl mx-auto px-6 md:px-10 py-4 flex items-center justify-between gap-4">
        <Link to="/" className="flex items-center gap-2 group" data-testid="nav-logo">
          <div className="bg-[#FF6B35] border-2 border-[#121212] rounded-xl w-9 h-9 flex items-center justify-center pp-shadow-sm group-hover:rotate-[-6deg] transition-transform">
            <Sparkles size={18} strokeWidth={3} color="#121212" />
          </div>
          <div className="flex flex-col leading-none">
            <span className="font-black text-xl tracking-tight" style={{ fontFamily: "Outfit" }}>
              TrendyPrompts
            </span>
            <span className="text-[10px] font-semibold uppercase tracking-widest text-[#4A4A4A]">
              Trending prompt library
            </span>
          </div>
        </Link>

        <nav className="flex items-center gap-2">
          {!isAdmin ? (
            <Link
              to="/admin"
              data-testid="nav-admin-link"
              className="hidden sm:inline-flex pp-chip"
            >
              Admin
            </Link>
          ) : (
            <Link to="/" data-testid="nav-back-home" className="pp-chip">
              ← Back to library
            </Link>
          )}
          {/*
            NOTE: there is no real "submit your own prompt" feature/backend
            yet (the original build, no user auth, public read-only +
            admin curation). The original button linked out to emergent.sh,
            which made no sense for a published app — replaced here with a
            mailto link as a safe default. Swap href for a real submission
            form/route if you build that feature later.
          */}
          <a
            href="https://docs.google.com/forms/d/e/1FAIpQLSdb1Pf4bCBVU3E6aexpgPySB9XSo2SzK8o4PZjs4IPIuYmWsA/viewform?usp=header"
            data-testid="nav-cta"
            className="inline-flex items-center gap-2 bg-[#121212] text-white font-semibold border-2 border-[#121212] rounded-full px-4 py-2 pp-shadow-sm pp-press hover:bg-[#FFBF00] hover:text-[#121212] transition-colors text-sm"
          >
            Drop a prompt
          </a>
        </nav>
      </div>
    </header>
  );
};

export default Navbar;
