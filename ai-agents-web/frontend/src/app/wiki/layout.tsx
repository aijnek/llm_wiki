import { WikiSidebar } from "@/components/WikiSidebar";

export default function WikiLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen bg-canvas">
      <WikiSidebar />
      <div className="flex-1 overflow-y-auto min-w-0">
        {children}
      </div>
    </div>
  );
}
