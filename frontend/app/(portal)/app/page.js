import { WorkspaceShell } from "@/components/workspace/WorkspaceShell";

export const metadata = {
  title: "Workspace · Folio",
};

export default function WorkspacePage() {
  return (
    <div className="h-[calc(100vh-3rem)]">
      <WorkspaceShell />
    </div>
  );
}
