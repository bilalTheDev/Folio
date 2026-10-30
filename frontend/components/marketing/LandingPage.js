"use client";

import Link from "next/link";
import { useState } from "react";
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
    a: "Raw files are discarded after text extraction. Folio keeps only chunks, embeddings, and chat history you choose to retain.",
  },
  {
    q: "Which file formats and sizes are supported?",
    a: "PDF, DOCX, and TXT up to 10 MB and 100 pages. Scanned image-only PDFs are not supported yet.",
  },
  {
    q: "How does Bring Your Own Key (BYOK) work?",
    a: "You paste a free key from Groq, Cerebras, Novita, or Hugging Face. Folio never pays for your inference and never logs the key.",
  },
];

function FaqItem({ item }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border-b border-[var(--hairline)]">
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
        <p className="pb-5 text-sm text-[var(--text-secondary)]">{item.a}</p>
      ) : null}
    </div>
  );
}

function HeroPreview() {
  return (
    <div className="glass mx-auto mt-14 max-w-3xl overflow-hidden rounded-[20px] shadow-[var(--shadow-soft)]">
      <div className="border-b border-[var(--hairline)] px-5 py-3 text-xs text-[var(--text-muted)]">
        Q3 Financial Analysis · Verified · Groq Llama 3.3
      </div>
      <div className="space-y-4 p-5">
        <div className="ml-auto max-w-[85%] rounded-[14px] bg-[var(--surface-2)] px-4 py-3 text-sm">
          What was the net impact of foreign exchange fluctuations in Section A.2?
        </div>
        <div className="max-w-[92%] rounded-[14px] border border-[var(--hairline)] bg-[var(--bg-elevated)] px-4 py-3 text-sm leading-relaxed text-[var(--text-secondary)]">
          FX translation reduced international operating income by roughly 240 bps, with EMEA logistics amplifying the effect.{" "}
          <Badge tone="accent">[1]</Badge>{" "}
          <Badge tone="violet">[2]</Badge>
        </div>
        <div className="rounded-[12px] border border-[var(--accent)]/20 bg-[var(--accent-soft)] p-3">
          <p className="mono text-[10px] tracking-wider text-[var(--accent)] uppercase">
            Document citation · Page 12 · § 2
          </p>
          <p className="mt-2 text-xs text-[var(--text-secondary)]">
            “International segment operating margins contracted 240 bps, driven primarily by FX translation variances…”
          </p>
        </div>
      </div>
    </div>
  );
}

export function LandingPage() {
  const [tab, setTab] = useState("finance");

  return (
    <div className="folio-glow min-h-screen">
      <header className="glass sticky top-0 z-40">
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
            <Link href="/sign-in" className="text-sm text-[var(--text-secondary)] hover:text-[var(--text)]">
              Sign In
            </Link>
            <Link href="/try">
              <Button size="sm">Try Free</Button>
            </Link>
          </div>
        </div>
      </header>

      <section id="overview" className="mx-auto max-w-6xl px-5 pt-20 pb-10 text-center">
        <Badge tone="violet" className="mb-6">
          Introducing Folio — grounded document answers
        </Badge>
        <h1 className="display mx-auto max-w-3xl text-5xl leading-[1.05] text-[var(--text)] md:text-6xl">
          Ask the page.
        </h1>
        <p className="mx-auto mt-5 max-w-2xl text-base text-[var(--text-secondary)] md:text-lg">
          Upload any PDF, DOCX, or TXT and get instant, grounded answers with page citations. Bring your own free
          key for privacy and zero markup.
        </p>
        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          <Link href="/try">
            <Button size="lg">Try Folio</Button>
          </Link>
          <a href="#grounding">
            <Button size="lg" variant="secondary">
              View Features
            </Button>
          </a>
        </div>
        <HeroPreview />
      </section>

      <section id="grounding" className="mx-auto max-w-6xl px-5 py-20">
        <h2 className="display text-center text-3xl md:text-4xl">
          Engineered for zero tolerance on false claims.
        </h2>
        <div className="mt-10 grid gap-4 md:grid-cols-3">
          {[
            {
              label: "Grounding",
              title: "Verifiable citations",
              body: "Every claim maps to a numbered passage with page and excerpt.",
            },
            {
              label: "Privacy",
              title: "Zero raw-file retention",
              body: "Uploaded bytes are discarded after extraction. Only chunks and vectors remain.",
            },
            {
              label: "BYOK",
              title: "Lightning BYOK engine",
              body: "Use free keys from Groq, Cerebras, Novita, or Hugging Face.",
            },
          ].map((card) => (
            <article
              key={card.title}
              className="rounded-[16px] border border-[var(--hairline)] bg-[var(--surface)] p-6"
            >
              <p className="mono text-[10px] tracking-[0.14em] text-[var(--accent)] uppercase">
                {card.label}
              </p>
              <h3 className="mt-3 text-lg text-[var(--text)]">{card.title}</h3>
              <p className="mt-2 text-sm text-[var(--text-secondary)]">{card.body}</p>
            </article>
          ))}
        </div>
      </section>

      <section id="cases" className="mx-auto max-w-6xl px-5 py-16">
        <h2 className="display text-center text-3xl">What you can ask Folio</h2>
        <div className="mt-6 flex justify-center gap-2">
          <Button
            size="sm"
            variant={tab === "finance" ? "primary" : "dark"}
            onClick={() => setTab("finance")}
          >
            Financial & Strategy
          </Button>
          <Button
            size="sm"
            variant={tab === "research" ? "primary" : "dark"}
            onClick={() => setTab("research")}
          >
            Technical & Research
          </Button>
        </div>
        <div className="glass mt-8 grid gap-0 overflow-hidden rounded-[20px] md:grid-cols-2">
          <div className="border-b border-[var(--hairline)] p-6 md:border-r md:border-b-0">
            <p className="text-xs text-[var(--text-muted)]">You</p>
            <p className="mt-3 text-sm">
              {tab === "finance"
                ? "Summarize the key drivers of margin contraction in the international segment."
                : "Which methods does the paper use for multi-head attention?"}
            </p>
          </div>
          <div className="p-6">
            <p className="text-xs text-[var(--accent)]">Source · Page {tab === "finance" ? "14" : "4"}</p>
            <p className="mt-3 text-sm text-[var(--text-secondary)]">
              {tab === "finance"
                ? "International segment operating margins contracted 240 bps, driven primarily by FX translation variances and elevated logistics costs in EMEA."
                : "Multi-head attention linearly projects queries, keys, and values h times with different learned projections, then concatenates."}
            </p>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-5 py-10">
        <div className="grid gap-6 rounded-[16px] border border-[var(--hairline)] bg-[var(--surface)] px-6 py-8 text-center md:grid-cols-3 md:text-left">
          <div>
            <p className="display text-3xl text-[var(--text)]">10 MB</p>
            <p className="mt-1 text-sm text-[var(--text-secondary)]">per file upload</p>
          </div>
          <div>
            <p className="display text-3xl text-[var(--text)]">100</p>
            <p className="mt-1 text-sm text-[var(--text-secondary)]">pages per document</p>
          </div>
          <div>
            <p className="display text-3xl text-[var(--text)]">200</p>
            <p className="mt-1 text-sm text-[var(--text-secondary)]">questions a day</p>
          </div>
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
            <Button size="lg">Try it Free</Button>
          </Link>
          <Link href="/sign-in">
            <Button size="lg" variant="secondary">
              Sign in
            </Button>
          </Link>
        </div>
      </section>

      <footer className="border-t border-[var(--hairline)]">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-5 py-8 md:flex-row md:items-center md:justify-between">
          <Logo />
          <div className="flex flex-wrap gap-5 text-sm text-[var(--text-secondary)]">
            <Link href="/privacy">Privacy</Link>
            <Link href="/terms">Terms</Link>
            <a href="https://github.com/bilalTheDev/Folio" target="_blank" rel="noreferrer">
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
