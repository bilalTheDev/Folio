export const DOCUMENTS = [
  {
    id: "doc-1",
    title: "Q3_Financial_Analysis_2024.pdf",
    pages: 42,
    updated: "2h ago",
    active: true,
  },
  {
    id: "doc-2",
    title: "Vaswani_Attention_Is_All_You_Need.pdf",
    pages: 15,
    updated: "Yesterday",
    active: false,
  },
  {
    id: "doc-3",
    title: "Clinical_Trial_Protocol_v3.pdf",
    pages: 88,
    updated: "3d ago",
    active: false,
  },
];

export const SOURCES = [
  {
    marker: 1,
    page: 14,
    location: "Paragraph 3",
    excerpt:
      "International segment operating margins contracted 240 bps, driven primarily by FX translation variances and elevated logistics costs in EMEA.",
    score: 0.96,
  },
  {
    marker: 2,
    page: 22,
    location: "Table 4.1",
    excerpt:
      "Distribution logistics overhead rose 18% YoY as capacity constraints forced premium freight utilization across secondary hubs.",
    score: 0.89,
  },
  {
    marker: 3,
    page: 6,
    location: "Section 2",
    excerpt:
      "North American manufacturing scale partially offset international pressure through fixed-cost absorption and supplier renegotiation.",
    score: 0.82,
  },
];

export const MEMBERS = [
  {
    name: "Dr. Clara Vance",
    email: "c.vance@biosynthetica.org",
    role: "Owner",
    keys: "Cerebras-v3",
    dossiers: 24,
    verified: "2m ago",
    status: "Active",
  },
  {
    name: "Elena Rostova, PhD",
    email: "e.rostova@biosynthetica.org",
    role: "Admin",
    keys: "Groq-Llama-70b",
    dossiers: 18,
    verified: "14m ago",
    status: "Active",
  },
  {
    name: "Marcus Chen",
    email: "m.chen@biosynthetica.org",
    role: "Analyst",
    keys: "Groq-8b",
    dossiers: 9,
    verified: "1h ago",
    status: "Active",
  },
  {
    name: "Priya Nair",
    email: "p.nair@biosynthetica.org",
    role: "Viewer",
    keys: "—",
    dossiers: 3,
    verified: "Yesterday",
    status: "Invited",
  },
];

export const AUDIT = [
  {
    time: "14:38:12 UTC",
    tag: "Security",
    action: "Enabled Mandatory Enterprise SSO",
    actor: "C. Vance",
    ip: "52.14.88.201",
  },
  {
    time: "14:22:04 UTC",
    tag: "BYOK",
    action: "Rotated Cerebras Ultra-Fast Endpoint Key",
    actor: "E. Rostova",
    ip: "18.220.11.44",
  },
  {
    time: "13:57:41 UTC",
    tag: "Sanitize",
    action: "Purged ephemeral vector cache (24h cycle)",
    actor: "System",
    ip: "internal",
  },
  {
    time: "13:41:09 UTC",
    tag: "Identity",
    action: "Invited p.nair@biosynthetica.org as Viewer",
    actor: "C. Vance",
    ip: "52.14.88.201",
  },
];
