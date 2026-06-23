import React, { useEffect, useMemo, useState } from "react";
import { Search, ChevronDown } from "lucide-react";
import { Navbar } from "../components/Navbar";
import { Filters } from "../components/Filters";
import { PromptCard } from "../components/PromptCard";
import { PromptModal } from "../components/PromptModal";
import { fetchPrompts, fetchMeta } from "../lib/api";

const HERO_TAGS = [
  "TikTok 🔥",
  "Y2K Chrome",
  "Cinematic Stills",
  "Pastel Surreal",
  "Lo-Fi Real",
  "Cyberpunk Neon",
  "Anime Hero",
  "Founder Mode",
  "Vlog B-Roll",
];

export default function LibraryPage() {
  const [meta, setMeta] = useState({ styles: [], platforms: [], use_cases: [] });
  const [filter, setFilter] = useState({ style: "All", platform: "All", use_case: "All" });
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [prompts, setPrompts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [active, setActive] = useState(null);
  const [showFilters, setShowFilters] = useState(true);

  // Debounce search
  useEffect(() => {
    const t = setTimeout(() => setDebouncedSearch(search.trim()), 250);
    return () => clearTimeout(t);
  }, [search]);

  // Load meta once
  useEffect(() => {
    fetchMeta().then(setMeta).catch(() => {});
  }, []);

  // Re-fetch prompts when filters or search change
  useEffect(() => {
    setLoading(true);
    const params = {};
    if (filter.style && filter.style !== "All") params.style = filter.style;
    if (filter.platform && filter.platform !== "All") params.platform = filter.platform;
    if (filter.use_case && filter.use_case !== "All") params.use_case = filter.use_case;
    if (debouncedSearch) params.search = debouncedSearch;
    fetchPrompts(params)
      .then((data) => setPrompts(data))
      .finally(() => setLoading(false));
  }, [filter, debouncedSearch]);

  const trendingCount = useMemo(
    () => prompts.filter((p) => (p.hotness || 0) >= 5).length,
    [prompts]
  );

  return (
    <div className="min-h-screen bg-[#F9F8F6]">
      <Navbar />

      {/* Hero */}
      <section className="relative border-b-2 border-[#121212] overflow-hidden">
        <div className="pp-dot-grid absolute inset-0" />
        <div className="max-w-7xl mx-auto px-6 md:px-10 pt-14 pb-12 relative">
          <div className="flex flex-wrap gap-2 mb-5">
            <span className="inline-flex items-center gap-2 bg-[#FFBF00] border-2 border-[#121212] rounded-full px-3 py-1 text-xs font-bold uppercase tracking-wider pp-shadow-xs pp-wobble">
              ★ New: 2026 trending pack
            </span>
            <span className="inline-flex items-center gap-2 bg-white border-2 border-[#121212] rounded-full px-3 py-1 text-xs font-bold uppercase tracking-wider">
              {prompts.length} prompts · {trendingCount} viral
            </span>
          </div>
          <h1
            className="text-5xl sm:text-6xl lg:text-7xl font-black leading-[0.95] max-w-4xl"
            style={{ fontFamily: "Outfit" }}
            data-testid="hero-title"
          >
            Drop your selfie.{" "}
            <span
              className="px-2 inline-block -rotate-1 border-2 border-[#121212] bg-[#FF6B35] text-white pp-shadow-sm"
            >
              Paste this.
            </span>{" "}
            Done.
          </h1>
          <p className="mt-5 text-lg max-w-2xl text-[#4A4A4A]">
            A loud, lovable library of trending AI image &amp; video prompts —
            curated for creators, founders, fashion heads, gamers and music artists.
          </p>
        </div>

        {/* Marquee strip */}
        <div className="border-t-2 border-[#121212] bg-[#121212] text-white py-3 overflow-hidden">
          <div className="pp-marquee text-sm font-bold uppercase tracking-widest">
            {[...HERO_TAGS, ...HERO_TAGS].map((t, i) => (
              <span key={i} className="flex items-center gap-3">
                <span className="opacity-60">✦</span>
                <span>{t}</span>
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* Search bar */}
      <section className="max-w-7xl mx-auto px-6 md:px-10 pt-10">
        <div className="flex items-center gap-3 max-w-2xl">
          <div className="relative flex-1">
            <Search
              size={20}
              strokeWidth={2.5}
              className="absolute left-5 top-1/2 -translate-y-1/2 text-[#121212]"
            />
            <input
              data-testid="search-input"
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by vibe, tag, or style…"
              className="w-full bg-white border-2 border-[#121212] rounded-full pl-12 pr-5 py-3.5 text-base font-medium pp-shadow placeholder:text-[#4A4A4A]/60 focus:outline-none focus:translate-x-[2px] focus:translate-y-[2px] focus:shadow-[4px_4px_0px_#121212] transition-all"
            />
          </div>
          <button
            data-testid="toggle-filters-button"
            onClick={() => setShowFilters((s) => !s)}
            className="md:hidden pp-chip"
          >
            Filters
            <ChevronDown
              size={14}
              className={`inline ml-1 transition-transform ${showFilters ? "rotate-180" : ""}`}
            />
          </button>
        </div>
      </section>

      {/* Filters + Grid */}
      <section className="max-w-7xl mx-auto px-6 md:px-10 py-8 grid grid-cols-1 md:grid-cols-[260px_1fr] gap-8">
        <aside
          className={`${showFilters ? "block" : "hidden"} md:block`}
          data-testid="filters-sidebar"
        >
          <div className="bg-white border-2 border-[#121212] rounded-2xl p-5 pp-shadow sticky top-24">
            <Filters meta={meta} value={filter} onChange={setFilter} />
            <button
              data-testid="reset-filters-button"
              onClick={() => {
                setFilter({ style: "All", platform: "All", use_case: "All" });
                setSearch("");
              }}
              className="mt-6 w-full bg-white text-[#121212] font-semibold border-2 border-[#121212] rounded-full px-4 py-2 pp-shadow-sm pp-press hover:bg-[#FFBF00] transition-colors text-sm"
            >
              Reset all
            </button>
          </div>
        </aside>

        <div>
          {loading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-7">
              {Array.from({ length: 6 }).map((_, i) => (
                <div
                  key={i}
                  className="pp-card h-[360px] animate-pulse bg-[#f4f4f4]"
                  data-testid={`skeleton-${i}`}
                />
              ))}
            </div>
          ) : prompts.length === 0 ? (
            <div
              data-testid="empty-state"
              className="bg-white border-2 border-[#121212] rounded-2xl p-10 text-center pp-shadow"
            >
              <p className="text-2xl font-black mb-2" style={{ fontFamily: "Outfit" }}>
                No prompts match.
              </p>
              <p className="text-[#4A4A4A]">Try clearing a filter or different keywords.</p>
            </div>
          ) : (
            <div
              data-testid="prompt-grid"
              className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-7"
            >
              {prompts.map((p, idx) => (
                <PromptCard key={p.id} card={p} onOpen={setActive} index={idx} />
              ))}
            </div>
          )}
        </div>
      </section>

      <footer className="border-t-2 border-[#121212] mt-10 bg-[#121212] text-white">
        <div className="max-w-7xl mx-auto px-6 md:px-10 py-8 flex flex-wrap items-center justify-between gap-3 text-sm">
          <span className="font-bold" style={{ fontFamily: "Outfit" }}>
            TrendyPrompts · Curated, copy-paste, ship today.
          </span>
          <span className="opacity-70">Made for creators · 2026</span>
        </div>
      </footer>

      <PromptModal card={active} onClose={() => setActive(null)} />
    </div>
  );
}
