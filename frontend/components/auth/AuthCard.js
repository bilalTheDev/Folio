"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Logo } from "@/components/brand/Logo";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";

export function AuthCard({ mode = "sign-in" }) {
  const router = useRouter();
  const [active, setActive] = useState(mode);
  const isSignIn = active === "sign-in";

  function onSubmit(event) {
    event.preventDefault();
    router.push("/app");
  }

  return (
    <div className="folio-auth-glow flex min-h-screen flex-col items-center justify-center p-6">
      <div className="w-full max-w-md rounded-2xl border border-white/[0.08] bg-[var(--surface)] p-8 shadow-[var(--shadow-2xl)]">
        <div className="flex justify-center">
          <Logo withWordmark={false} size={40} />
        </div>
        <h1 className="display mt-6 text-center text-3xl text-[var(--text)]">
          {isSignIn ? "Return to your documents" : "Begin reading with precision"}
        </h1>
        <p className="mt-3 text-center text-sm text-[var(--text-secondary)]">
          A focused sanctuary for legal, technical, and deep research synthesis.
        </p>

        <div className="mt-6 grid grid-cols-2 rounded-full bg-[var(--bg-chrome)] p-1">
          <button
            type="button"
            className={`rounded-full py-2 text-sm transition ${
              isSignIn
                ? "bg-[var(--accent)] text-[var(--accent-ink)]"
                : "text-[var(--text-secondary)]"
            }`}
            onClick={() => setActive("sign-in")}
          >
            Sign In
          </button>
          <button
            type="button"
            className={`rounded-full py-2 text-sm transition ${
              !isSignIn
                ? "bg-[var(--accent)] text-[var(--accent-ink)]"
                : "text-[var(--text-secondary)]"
            }`}
            onClick={() => setActive("sign-up")}
          >
            Create Account
          </button>
        </div>

        <div className="mt-5 grid grid-cols-2 gap-3">
          <Button variant="dark" className="w-full" type="button">
            Google
          </Button>
          <Button variant="dark" className="w-full" type="button">
            GitHub
          </Button>
        </div>

        <div className="mono my-5 flex items-center gap-3 text-[10px] tracking-[0.16em] text-[var(--text-muted)]">
          <span className="h-px flex-1 bg-white/[0.08]" />
          OR WITH CREDENTIALS
          <span className="h-px flex-1 bg-white/[0.08]" />
        </div>

        <form className="space-y-4" onSubmit={onSubmit}>
          <Input
            label="Email Address"
            type="email"
            name="email"
            placeholder="scholar@institute.edu"
            required
          />
          <Input
            label="Password"
            type="password"
            name="password"
            placeholder="••••••••••••"
            required
            hint={
              isSignIn ? (
                <Link
                  href="#"
                  className="normal-case tracking-normal text-[var(--text-muted)] hover:text-[var(--text-secondary)]"
                >
                  Forgot code?
                </Link>
              ) : null
            }
          />
          {!isSignIn ? (
            <Input
              label="Display Name"
              type="text"
              name="name"
              placeholder="Elena Rostova"
              required
            />
          ) : null}
          <Button type="submit" className="mt-2 w-full" size="lg">
            {isSignIn ? "Enter Workspace →" : "Create Workspace →"}
          </Button>
        </form>

        <p className="mono mt-5 text-center text-[10px] tracking-[0.14em] text-[var(--text-muted)]">
          END-TO-END ENCRYPTED · SOC2 TYPE II · BYOK READY
        </p>
      </div>

      <p className="mono mt-8 flex items-center gap-2 text-[11px] text-[var(--text-muted)]">
        <span className="live-dot h-1.5 w-1.5 rounded-full bg-[var(--accent)]" />
        Cluster US-East · Isolated Reading Node
      </p>
    </div>
  );
}
