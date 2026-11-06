import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";

const STATUS = {
  uploaded: { tone: "neutral", label: "Uploaded" },
  indexing: { tone: "info", label: "Indexing" },
  indexed: { tone: "success", label: "Indexed" },
  failed: { tone: "danger", label: "Failed" },
};

export default function StatusBadge({ status }) {
  const meta = STATUS[status] || STATUS.uploaded;
  return (
    <Badge tone={meta.tone}>
      {status === "indexing" && <Spinner className="size-3" />}
      {meta.label}
    </Badge>
  );
}
