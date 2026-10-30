"use client";

import { useMemo, useState } from "react";
import { AUDIT, MEMBERS } from "@/lib/mock-data";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Toggle } from "@/components/ui/Toggle";

export function AdminPortal() {
  const [filter, setFilter] = useState("all");
  const [sso, setSso] = useState(true);
  const [autoPurge, setAutoPurge] = useState(true);
  const [query, setQuery] = useState("");

  const members = useMemo(() => {
    return MEMBERS.filter((member) => {
      const matchesFilter =
        filter === "all" ? true : member.status.toLowerCase() === "invited";
      const haystack = `${member.name} ${member.email}`.toLowerCase();
      return matchesFilter && haystack.includes(query.toLowerCase());
    });
  }, [filter, query]);

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-5 py-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="mono text-[10px] tracking-[0.14em] text-[var(--text-muted)] uppercase">
            Enterprise Tenant · Tier 3 Isolated Enclave
          </p>
          <h1 className="display mt-2 text-3xl text-[var(--text)]">Organization Administration</h1>
          <div className="mt-2 flex flex-wrap items-center gap-2">
            <p className="text-sm text-[var(--text-secondary)]">BioSynthetica Research Labs</p>
            <Badge tone="accent">SOC2 Type II Active</Badge>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary">Compliance Manifest</Button>
          <Button>+ Invite Member</Button>
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {[
          {
            label: "Active Seats",
            value: "18 / 25",
            meta: "7 unallocated float tokens",
            bar: 72,
          },
          {
            label: "Grounded Queries",
            value: "48,290",
            meta: "99.8% single-passage proof",
          },
          {
            label: "Vector Ephemeral Cache",
            value: "1.4 GB",
            meta: "24h cycle flush",
          },
          {
            label: "BYOK Inference Cost",
            value: "$0.00",
            meta: "100% direct Groq & Cerebras keys",
          },
        ].map((card) => (
          <article
            key={card.label}
            className="rounded-[16px] border border-[var(--hairline)] bg-[var(--surface)] p-4"
          >
            <p className="mono text-[10px] tracking-[0.12em] text-[var(--text-muted)] uppercase">
              {card.label}
            </p>
            <p className="display mt-3 text-2xl text-[var(--text)]">{card.value}</p>
            <p className="mt-1 text-xs text-[var(--text-secondary)]">{card.meta}</p>
            {card.bar ? (
              <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-white/10">
                <div
                  className="h-full rounded-full bg-[var(--accent)]"
                  style={{ width: `${card.bar}%` }}
                />
              </div>
            ) : null}
          </article>
        ))}
      </div>

      <div className="grid gap-5 xl:grid-cols-[1.6fr_1fr]">
        <section className="rounded-[16px] border border-[var(--hairline)] bg-[var(--surface)] p-4">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-base text-[var(--text)]">Workspace Members</h2>
            <div className="flex flex-wrap gap-2">
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Filter scholar..."
                className="h-9 rounded-[10px] border border-[var(--hairline)] bg-[var(--bg-elevated)] px-3 text-sm outline-none"
              />
              <Button
                size="sm"
                variant={filter === "all" ? "primary" : "dark"}
                onClick={() => setFilter("all")}
              >
                All (18)
              </Button>
              <Button
                size="sm"
                variant={filter === "invited" ? "primary" : "dark"}
                onClick={() => setFilter("invited")}
              >
                Invited (2)
              </Button>
            </div>
          </div>

          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead className="mono text-[10px] tracking-[0.1em] text-[var(--text-muted)] uppercase">
                <tr>
                  <th className="pb-3 font-medium">Member</th>
                  <th className="pb-3 font-medium">Role</th>
                  <th className="pb-3 font-medium">Active Keys</th>
                  <th className="pb-3 font-medium">Dossiers</th>
                  <th className="pb-3 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {members.map((member) => (
                  <tr key={member.email} className="border-t border-[var(--hairline)]">
                    <td className="py-3">
                      <p className="text-[var(--text)]">{member.name}</p>
                      <p className="text-xs text-[var(--text-muted)]">{member.email}</p>
                    </td>
                    <td className="py-3 text-[var(--text-secondary)]">{member.role}</td>
                    <td className="py-3 text-[var(--text-secondary)]">{member.keys}</td>
                    <td className="py-3 text-[var(--text-secondary)]">{member.dossiers}</td>
                    <td className="py-3">
                      <Badge tone={member.status === "Active" ? "accent" : "warning"}>
                        {member.status}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <div className="space-y-5">
          <section className="rounded-[16px] border border-[var(--hairline)] bg-[var(--surface)] p-4">
            <h2 className="text-base text-[var(--text)]">Security Policies</h2>
            <div className="mt-4 space-y-4">
              <Toggle
                checked={sso}
                onChange={setSso}
                label="Mandatory Enterprise SSO"
                description="Require IdP login for all seats."
              />
              <Toggle
                checked={autoPurge}
                onChange={setAutoPurge}
                label="Vector Memory Auto-Purge"
                description="Flush ephemeral cache on 24h cycle."
              />
              <div className="rounded-[12px] border border-[var(--hairline)] bg-[var(--bg-elevated)] px-3 py-3">
                <p className="mono text-[10px] tracking-[0.1em] text-[var(--text-muted)] uppercase">
                  Authorized Email Domain
                </p>
                <p className="mt-1 text-sm text-[var(--text)]">@biosynthetica.org</p>
              </div>
              <Button variant="secondary" className="w-full">
                Export Verified Ledger (JSON)
              </Button>
            </div>
          </section>

          <section className="rounded-[16px] border border-[var(--hairline)] bg-[var(--surface)] p-4">
            <h2 className="text-base text-[var(--text)]">Inference Gateway</h2>
            <p className="mt-2 text-sm text-[var(--text-secondary)]">Groq LPUs + Cerebras CS-3</p>
            <p className="mono mt-2 text-[11px] text-[var(--accent)]">p99 &lt; 814ms</p>
          </section>
        </div>
      </div>

      <section className="rounded-[16px] border border-[var(--hairline)] bg-[var(--surface)] p-4">
        <h2 className="text-base text-[var(--text)]">Workspace Quotas & Rate Shields</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {[
            {
              title: "Per-User Document Limit",
              value: "100 MB / 500 pgs",
              meta: "Automatic compression enforced",
            },
            {
              title: "Simultaneous Query Streams",
              value: "16 Streams / seat",
              meta: "Contemplative throttle nominal",
            },
            {
              title: "Inference Ceiling",
              value: "120 TPM peak",
              meta: "Zero drop-spillover active",
            },
          ].map((item) => (
            <div
              key={item.title}
              className="rounded-[12px] border border-[var(--hairline)] bg-[var(--bg-elevated)] p-3"
            >
              <p className="text-xs text-[var(--text-muted)]">{item.title}</p>
              <p className="mt-2 text-sm text-[var(--text)]">{item.value}</p>
              <p className="mt-1 text-[11px] text-[var(--text-secondary)]">{item.meta}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-[16px] border border-[var(--hairline)] bg-[var(--surface)] p-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base text-[var(--text)]">Recent Audit Trail</h2>
          <Badge tone="accent">Streaming Live Records</Badge>
        </div>
        <div className="mt-4 space-y-3">
          {AUDIT.map((row) => (
            <div
              key={`${row.time}-${row.action}`}
              className="grid gap-2 border-t border-[var(--hairline)] pt-3 md:grid-cols-[140px_100px_1fr_120px]"
            >
              <p className="mono text-[11px] text-[var(--text-muted)]">{row.time}</p>
              <Badge tone="violet">{row.tag}</Badge>
              <p className="text-sm text-[var(--text-secondary)]">{row.action}</p>
              <p className="mono text-[11px] text-[var(--text-muted)]">
                {row.actor} · {row.ip}
              </p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
