"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { ChatHeader, ComposerDock, IndexingNotice } from "@/components/chat/ChatLayoutParts";
import Composer from "@/components/chat/Composer";
import Alert from "@/components/ui/Alert";
import Atmosphere from "@/components/ui/Atmosphere";
import { queueFirstMessage } from "@/hooks/useChat";
import { useSessionsStore } from "@/hooks/useSessions";
import { getErrorMessage } from "@/lib/api";

const SUGGESTIONS = [
  "Summarize the key points of my documents.",
  "What are the main risks or open issues mentioned?",
  "List the important dates and deadlines.",
  "Which sections talk about pricing or costs?",
];

export default function NewChat() {
  const router = useRouter();
  const createSession = useSessionsStore((s) => s.create);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

  const start = async (content) => {
    setCreating(true);
    setError("");
    try {
      const session = await createSession();
      queueFirstMessage(session.id, content);
      router.push(`/app/chat/${session.id}`);
    } catch (err) {
      setError(getErrorMessage(err, "Couldn't start a new chat. Please try again."));
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <ChatHeader title="New chat" />
      <div className="relative min-h-0 flex-1 overflow-y-auto">
        <Atmosphere
          orbs={[
            { color: "mint", size: 380, left: "8%", top: "-18%", opacity: 0.4 },
            { color: "peach", size: 280, left: "62%", top: "8%", opacity: 0.3 },
            { color: "lavender", size: 240, left: "28%", top: "58%", opacity: 0.28 },
          ]}
        />
        <div className="relative mx-auto flex max-w-2xl flex-col items-center px-6 py-10 pb-8 text-center sm:py-14">
          <p className="caption-upper text-muted">New conversation</p>
          <h2 className="display-lg mt-4 text-ink">What do you want to know?</h2>
          <p className="mt-4 max-w-md text-[15px] leading-relaxed text-body">
            Ask anything about your uploaded documents. Every answer links back to the passages it came from.
          </p>
          <div className="mt-8 grid w-full gap-3 sm:grid-cols-2">
            {SUGGESTIONS.map((text) => (
              <button
                key={text}
                onClick={() => start(text)}
                disabled={creating}
                className="rounded-2xl border border-hairline bg-card px-5 py-5 text-left text-[15px] leading-relaxed text-body transition-shadow hover:shadow-soft disabled:opacity-50"
              >
                {text}
              </button>
            ))}
          </div>
          <Alert className="mt-6 w-full text-left">{error}</Alert>
        </div>
      </div>
      <ComposerDock>
        <IndexingNotice />
        <Composer onSend={start} busy={creating} autoFocus />
      </ComposerDock>
    </div>
  );
}
