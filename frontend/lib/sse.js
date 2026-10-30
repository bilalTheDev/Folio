import { apiFetch } from "@/lib/api";

/**
 * Parse a Server-Sent Events stream from a fetch Response.
 * Calls onEvent(eventName, dataObject) for each event.
 */
export async function readSse(response, { onEvent, signal } = {}) {
  if (!response.ok || !response.body) {
    const text = await response.text().catch(() => "");
    let message = text || `Request failed (${response.status})`;
    try {
      const parsed = JSON.parse(text);
      message = parsed?.detail?.message || parsed?.message || message;
    } catch {
      // keep raw
    }
    const err = new Error(message);
    err.status = response.status;
    throw err;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let eventName = "message";
  let dataLines = [];

  const flush = () => {
    if (!dataLines.length) return;
    const raw = dataLines.join("\n");
    dataLines = [];
    let parsed = raw;
    try {
      parsed = JSON.parse(raw);
    } catch {
      // keep raw string
    }
    onEvent?.(eventName, parsed);
    eventName = "message";
  };

  while (true) {
    if (signal?.aborted) {
      await reader.cancel();
      break;
    }
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n");
    buffer = parts.pop() || "";
    for (const line of parts) {
      if (line.startsWith("event:")) {
        eventName = line.slice(6).trim();
      } else if (line.startsWith("data:")) {
        dataLines.push(line.slice(5).trim());
      } else if (line.trim() === "") {
        flush();
      }
    }
  }
  flush();
}

function mapCitations(payload) {
  const items = payload?.items || payload || [];
  return items.map((item) => ({
    marker: item.marker,
    page: item.page,
    location: item.location || `Page ${item.page}`,
    excerpt: item.excerpt,
    score: item.score,
  }));
}

async function consumeAnswerStream(response, { onMeta, onCitations, onToken, onDone, onError, signal }) {
  let sawDone = false;
  await readSse(response, {
    signal,
    onEvent: (event, data) => {
      if (event === "meta") onMeta?.(data);
      else if (event === "citations") onCitations?.(mapCitations(data));
      else if (event === "token") onToken?.(data?.text ?? "");
      else if (event === "done") {
        sawDone = true;
        onDone?.(data);
      } else if (event === "error") onError?.(data);
    },
  });
  if (!sawDone && !signal?.aborted) onDone?.({ stopped: false });
}

/** Live sample-document trial stream (auth-free, IP-limited). */
export async function sampleAnswerStream(question, handlers = {}) {
  const controller = handlers.signal ? null : new AbortController();
  const signal = handlers.signal || controller.signal;
  const response = await apiFetch("/sample/messages", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content: question, provider: "groq" }),
    signal,
  });
  await consumeAnswerStream(response, { ...handlers, signal });
  return { abort: () => controller?.abort() };
}

/** Authenticated thread question stream. */
export async function threadAnswerStream(threadId, question, handlers = {}) {
  const controller = handlers.signal ? null : new AbortController();
  const signal = handlers.signal || controller.signal;
  const response = await apiFetch(`/threads/${threadId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      content: question,
      provider: "groq",
      regenerate: Boolean(handlers.regenerate),
    }),
    signal,
  });
  await consumeAnswerStream(response, { ...handlers, signal });
  return { abort: () => controller?.abort() };
}

/** Demo stream for portfolio UI when no live API key/session is available. */
export async function demoAnswerStream(question, { onToken, onCitations, onDone, signal } = {}) {
  const answer =
    "International operating margins contracted about 240 bps. The primary drivers were FX " +
    "translation variances in EMEA [1] and elevated distribution logistics overhead [2]. " +
    "North American manufacturing scale partially offset the pressure [3].";

  onCitations?.([
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
  ]);

  const words = answer.split(/(\s+)/);
  for (const word of words) {
    if (signal?.aborted) break;
    onToken?.(word);
    await new Promise((r) => setTimeout(r, 18 + Math.random() * 28));
  }
  onDone?.({ demo: true, question, stopped: Boolean(signal?.aborted) });
}
