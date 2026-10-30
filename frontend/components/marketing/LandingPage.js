"use client";

import Link from "next/link";
import { useState } from "react";
import { motion } from "framer-motion";
import { Logo } from "@/components/brand/Logo";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";

const FAQS = [
  {
    q: "How does Folio guarantee zero hallucinations?",
    a: "Answers are generated only from retrieved passages in your document. If the context does not contain the answer, Folio says so instead of inventing one.",
  },
  {
    q: "Are my uploaded documents stored on a server?",
    a: "Raw files are discarded after text extraction. Folio keeps only chunks, embeddings, and chat history you choose to retain—never permanent original uploads.",
  },
  {
    q: "Which file formats and sizes are supported?",
    a: "PDF, DOCX, and TXT up to 10 MB and 100 pages. Scanned image-only PDFs are not supported yet.",
  },
  {
    q: "How does Bring Your Own Key (BYOK) work?",
    a: "Paste a free key from Groq, Cerebras, Novita, or Hugging Face. Folio never pays for your inference and never logs the key.",
  },
];

const SCENARIOS = {
  finance: {
    label: "Financial 10-K Filings",
    prompt: "What drove operating margin contraction in the international segment?",
    excerpt:
      "International segment operating margins contracted 240 bps, driven primarily by FX translation variances and elevated logistics costs in EMEA.",
    page: "Page 58 · Item 7 MD&A",
    latency: "480ms",
  },
  clinical: {
    label: "Clinical Research & Trials",
    prompt: "What was the primary endpoint success criterion in Cohort B?",
    excerpt:
      "Cohort B met the co-primary endpoint of ≥30% reduction in biomarker X at week 12 versus baseline (p < 0.01).",
    page: "Page 22 · Section 4.1",
    latency: "512ms",
  },
  legal: {
    label: "Legal SLAs & Contracts",
    prompt: "When may either party terminate for convenience?",
    excerpt:
      "Either party may terminate for convenience upon ninety (90) days’ prior written notice, subject to wind-down obligations in Schedule C.",
    page: "Page 11 · § 8.2",
    latency: "401ms",
  },
};

function FaqItem({ item }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border-b border-white/[0.06]">
      <button
        type="button"
        className="flex w-full items-center justify-between gap-4 py-5 text-left"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        <span className="text-[15px] text-[var(--text)]">{item.q}</span>
        <span className="text-[var(--text-muted)]">{open ? "−" : "+"}</span>
      </button>
      {open ? (
        <p className="fade-up pb-5 text-sm text-[var(--text-secondary)]">{item.a}</p>
      ) : null}
    </div>
  );
}

function EnginePreview() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1], delay: 0.15 }}
      className="mx-auto mt-14 max-w-3xl overflow-hidden rounded-xl border border-white/[0.08] bg-[var(--surface)] shadow-[var(--shadow-2xl)]"
    >
      <div className="flex items-center justify-between border-b border-white/[0.06] px-5 py-3">
        <p className="mono text-[11px] text-[var(--text-muted)]">
          Alphabet_Q4_Financial_Report.pdf
        </p>
        <Badge tone="accent">● 99.8% Grounding Confidence</Badge>
      </div>
      <div className="space-y-4 p-5">
        <div className="ml-auto max-w-[88%] rounded-lg bg-[var(--surface-elevated)] px-4 py-3 text-sm text-[var(--text)]">
          Folio, what is the key driver behind the bilateral margin fluctuations in Section A.2?
        </div>
        <div className="max-w-[92%] text-sm leading-relaxed text-[var(--text-secondary)]">
          FX translation reduced international operating income by roughly 240 bps, with EMEA
          logistics amplifying the effect.{" "}
          <span className="mx-0.5 inline-flex h-5 items-center rounded-md bg-[var(--accent-soft)] px-1.5 text-[11px] font-medium text-[var(--accent)]">
            [2]
          </span>
        </div>
        <div className="rounded-lg border border-[var(--accent)]/25 bg-[var(--accent-soft)] p-3">
          <p className="mono text-[10px] tracking-[0.14em] text-[var(--accent)] uppercase">
            Document Citation · Page 12 · § 2
          </p>
          <p className="mt-2 text-xs text-[var(--text-secondary)]">
            “International segment operating margins contracted 240 bps, driven primarily by FX
            translation variances…”
          </p>
        </div>
      </div>
    </motion.div>
  );
}

export function LandingPage() {
  const [tab, setTab] = useState("finance");
  const scenario = SCENARIOS[tab];

  return (
    <div className="folio-atmosphere min-h-screen">
      <header className="sticky top-0 z-40 border-b border-white/[0.05] bg-[#0D0D11]/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-5">
          <div className="flex items-center gap-8">
            <Link href="/">
              <Logo />
            </Link>
            <nav className="hidden items-center gap-6 text-sm text-[var(--text-secondary)] md:flex">
              <a href="#overview" className="hover:text-[var(--text)]">
                Overview
              </a>
              <a href="#grounding" className="hover:text-[var(--text)]">
                Grounding
              </a>
              <a href="#cases" className="hover:text-[var(--text)]">
                Use Cases
              </a>
              <a href="#faq" className="hover:text-[var(--text)]">
                FAQ
              </a>
            </nav>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/login"
              className="text-sm text-[var(--text-secondary)] hover:text-[var(--text)]"
            >
              Sign in
            </Link>
            <Link href="/try">
              <Button size="pill">Try it free</Button>
            </Link>
          </div>
        </div>
      </header>

      <section id="overview" className="mx-auto max-w-6xl px-5 pt-20 pb-8 text-center">
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
        >
          <span className="mono inline-flex items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.03] px-3 py-1 text-[11px] tracking-[0.12em] text-[var(--text-secondary)] uppercase">
            <span className="live-dot h-1.5 w-1.5 rounded-full bg-[var(--accent)]" />
            Deterministic Page Grounding Engine v2.4
          </span>
          <h1 className="display mx-auto mt-7 max-w-3xl text-5xl leading-[1.05] text-white md:text-6xl">
            Ask the page.
          </h1>
          <p className="mx-auto mt-5 max-w-2xl text-base text-[var(--text-secondary)] md:text-lg">
            Upload any PDF or research document. Receive precise answers backed by deterministic
            bounding boxes and citations you can verify instantly.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <a href="#grounding">
              <Button size="lg">How it works →</Button>
            </a>
            <Link href="/try">
              <Button size="lg" variant="secondary">
                Try it free
              </Button>
            </Link>
          </div>
        </motion.div>
        <EnginePreview />
      </section>

      <section id="grounding" className="mx-auto max-w-6xl px-5 py-20">
        <h2 className="display text-center text-3xl md:text-4xl">
          Engineered for zero tolerance on false claims.
        </h2>
        <div className="mt-10 grid gap-4 md:grid-cols-3">
          {[
            {
              n: "01",
              label: "Reproducibility",
              title: "Verifiable Grounding",
              body: "Pixel-aware citations to PDF pages and passages—every claim maps to a source you can open.",
            },
            {
              n: "02",
              label: "Security",
              title: "Zero-Retention Privacy",
              body: "Ephemeral in-memory vectorization. Raw files discarded after extraction. Zero model training on your data.",
            },
            {
              n: "03",
              label: "Performance",
              title: "Lightning BYOK Engine",
              body: "Direct Groq & Cerebras LPUs with your own free keys. Typical streams above 400 tok/sec.",
            },
          ].map((card, i) => (
            <motion.article
              key={card.title}
              initial={{ opacity: 0, y: 12 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-40px" }}
              transition={{ delay: i * 0.08, duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
              className="surface-card p-6"
            >
              <p className="mono text-[10px] tracking-[0.16em] text-[var(--accent)] uppercase">
                {card.n} · {card.label}
              </p>
              <h3 className="mt-3 text-lg text-[var(--text)]">{card.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-[var(--text-secondary)]">
                {card.body}
              </p>
            </motion.article>
          ))}
        </div>
      </section>

      <section id="cases" className="mx-auto max-w-6xl px-5 py-16">
        <h2 className="display text-center text-3xl">What you can ask Folio</h2>
        <div className="mt-6 flex flex-wrap justify-center gap-2">
          {Object.entries(SCENARIOS).map(([key, value]) => (
            <Button
              key={key}
              size="pill"
              variant={tab === key ? "primary" : "dark"}
              onClick={() => setTab(key)}
            >
              {value.label}
            </Button>
          ))}
        </div>
        <div className="mt-8 grid overflow-hidden rounded-xl border border-white/[0.08] bg-[var(--surface)] md:grid-cols-2">
          <div className="border-b border-white/[0.06] p-6 md:border-r md:border-b-0">
            <p className="mono text-[10px] tracking-[0.14em] text-[var(--text-muted)] uppercase">
              Prompt
            </p>
            <p className="mt-3 text-sm text-[var(--text)]">{scenario.prompt}</p>
            <p className="mono mt-4 text-[11px] text-[var(--accent)]">
              Latency · {scenario.latency}
            </p>
          </div>
          <div className="p-6">
            <p className="mono text-[10px] tracking-[0.14em] text-[var(--accent)] uppercase">
              Cited excerpt · {scenario.page}
            </p>
            <p className="mt-3 text-sm leading-relaxed text-[var(--text-secondary)]">
              “{scenario.excerpt}”
            </p>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-5 py-10">
        <div className="grid gap-8 rounded-xl border border-white/[0.08] bg-[var(--surface)] px-8 py-10 text-center md:grid-cols-3 md:text-left">
          {[
            { value: "10 MB", label: "per file upload" },
            { value: "100", label: "pages parsed per doc" },
            { value: "200", label: "daily queries included" },
          ].map((stat) => (
            <div key={stat.label}>
              <p className="display text-4xl text-[var(--text)]">{stat.value}</p>
              <p className="mt-2 text-sm text-[var(--text-secondary)]">{stat.label}</p>
            </div>
          ))}
        </div>
      </section>

      <section id="faq" className="mx-auto max-w-3xl px-5 py-16">
        <h2 className="display text-center text-3xl">Frequently Asked Questions</h2>
        <div className="mt-8">
          {FAQS.map((item) => (
            <FaqItem key={item.q} item={item} />
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-5 py-20 text-center">
        <h2 className="display text-4xl md:text-5xl">Start with a document.</h2>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <Link href="/try">
            <Button size="lg">Try it free</Button>
          </Link>
          <a href="#overview">
            <Button size="lg" variant="secondary">
              View sample citations
            </Button>
          </a>
        </div>
      </section>

      <footer className="border-t border-white/[0.06]">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-5 py-8 md:flex-row md:items-center md:justify-between">
          <Logo />
          <div className="flex flex-wrap gap-5 text-sm text-[var(--text-secondary)]">
            <Link href="/privacy">Privacy</Link>
            <Link href="/terms">Terms</Link>
            <a
              href="https://github.com/bilalTheDev/Folio"
              target="_blank"
              rel="noreferrer"
            >
              GitHub
            </a>
          </div>
        </div>
        <p className="mono px-5 pb-8 text-center text-[11px] text-[var(--text-muted)]">
          © {new Date().getFullYear()} Folio. Free to use. Bring your own key.
        </p>
      </footer>
    </div>
  );
}
