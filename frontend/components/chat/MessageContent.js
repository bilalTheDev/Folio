import { Fragment } from "react";

const INLINE = /(\*\*[^*\n]+\*\*|`[^`\n]+`|\[\d+\])/g;
const BULLET = /^\s*[-*•]\s+/;
const NUMBERED = /^\s*\d+[.)]\s+/;
const HEADING = /^\s*#{1,6}\s+/;

function Inline({ text, sourceCount, activeSource, onCite }) {
  return text.split(INLINE).map((part, i) => {
    if (!part) return null;
    if (part.startsWith("**") && part.endsWith("**")) return <strong key={i}>{part.slice(2, -2)}</strong>;
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code key={i} className="rounded-md bg-strong px-1 py-0.5 text-[0.9em]">
          {part.slice(1, -1)}
        </code>
      );
    }
    const cite = part.match(/^\[(\d+)\]$/);
    if (cite) {
      const n = Number(cite[1]);
      // Markers that don't map to a returned source are left as plain text.
      if (n < 1 || n > sourceCount) return <Fragment key={i}>{part}</Fragment>;
      const active = activeSource === n - 1;
      return (
        <button
          key={i}
          type="button"
          onClick={() => onCite(n - 1)}
          aria-label={`Show source ${n}`}
          aria-pressed={active}
          className={`mx-0.5 inline-grid h-[1.15rem] min-w-[1.15rem] place-items-center rounded-full px-1 align-[0.1em] text-[0.7rem] font-medium transition-colors ${
            active ? "bg-primary text-on-primary" : "bg-strong text-ink hover:bg-hairline"
          }`}
        >
          {n}
        </button>
      );
    }
    return <Fragment key={i}>{part}</Fragment>;
  });
}

// Groups lines into paragraphs, lists, and headings; enough for model answers without a markdown dependency.
function toBlocks(content) {
  const blocks = [];
  for (const raw of content.split("\n")) {
    const line = raw.trimEnd();
    const last = blocks[blocks.length - 1];
    if (!line.trim()) {
      blocks.push({ type: "break" });
    } else if (BULLET.test(line) || NUMBERED.test(line)) {
      const type = BULLET.test(line) ? "ul" : "ol";
      const item = line.replace(type === "ul" ? BULLET : NUMBERED, "");
      if (last?.type === type) last.items.push(item);
      else blocks.push({ type, items: [item] });
    } else if (HEADING.test(line)) {
      blocks.push({ type: "h", text: line.replace(HEADING, "") });
    } else if (last?.type === "p") {
      last.lines.push(line);
    } else {
      blocks.push({ type: "p", lines: [line] });
    }
  }
  return blocks.filter((b) => b.type !== "break");
}

export default function MessageContent({ content, sourceCount = 0, activeSource = null, onCite = () => {} }) {
  const inline = (text) => (
    <Inline text={text} sourceCount={sourceCount} activeSource={activeSource} onCite={onCite} />
  );

  return (
    <div className="space-y-3 text-[15px] leading-relaxed tracking-[0.01em] text-body">
      {toBlocks(content).map((block, i) => {
        if (block.type === "h") {
          return (
            <p key={i} className="font-medium text-ink">
              {inline(block.text)}
            </p>
          );
        }
        if (block.type === "ul" || block.type === "ol") {
          const List = block.type;
          return (
            <List key={i} className={`space-y-1 pl-5 ${block.type === "ul" ? "list-disc" : "list-decimal"}`}>
              {block.items.map((item, j) => (
                <li key={j}>{inline(item)}</li>
              ))}
            </List>
          );
        }
        return (
          <p key={i} className="whitespace-pre-wrap">
            {inline(block.lines.join("\n"))}
          </p>
        );
      })}
    </div>
  );
}
