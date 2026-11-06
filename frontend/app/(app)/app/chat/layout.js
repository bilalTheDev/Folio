import SessionSidebar from "@/components/layout/SessionSidebar";

export const instant = false;

export default function ChatLayout({ children }) {
  return (
    <div className="flex min-h-0 flex-1">
      <SessionSidebar />
      <div className="flex min-h-0 min-w-0 flex-1 flex-col">{children}</div>
    </div>
  );
}
