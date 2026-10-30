/**
 * Parse a Server-Sent Events stream from a fetch Response.
 * Calls onEvent(eventName, dataObject) for each event.
 */
export async function readSse(response, { onEvent, signal } = {}) {
  if (!response.ok || !response.body) {
    const text = await response.text().catch(() => "");
    throw new Error(text || `Request failed (${response.status})`);
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

/** Demo stream for portfolio UI when no live API key/session is available. */
export async function demoAnswerStream(question, { onToken, onCitations, onDone }) {
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
    onToken?.(word);
    await new Promise((r) => setTimeout(r, 18 + Math.random() * 28));
  }
  onDone?.({ demo: true, question });
}
