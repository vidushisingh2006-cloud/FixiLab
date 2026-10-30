import { createFileRoute, Link, Outlet } from "@tanstack/react-router";
import { Logo } from "@/components/landing/primitives";

export const Route = createFileRoute("/audit")({
  component: AuditLayout,
});

function AuditLayout() {
  return (
    <div className="min-h-screen bg-background">
      <header className="fixed inset-x-0 top-0 z-50 px-3 pt-3">
        <div className="mx-auto flex max-w-6xl items-center justify-between rounded-2xl border border-border bg-card/90 px-4 py-3 shadow-soft backdrop-blur-md">
          <Logo />
          <Link to="/" className="text-sm font-semibold text-foreground hover:text-primary">
            Back to Home
          </Link>
        </div>
      </header>

      <main className="pt-24 pb-16">
        <Outlet />
      </main>
    </div>
  );
}

