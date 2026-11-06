import Button from "@/components/ui/Button";
import Logo from "@/components/ui/Logo";
import ThemeToggle from "@/components/ui/ThemeToggle";

export default function NotFound() {
  return (
    <main className="flex flex-1 flex-col px-6 py-8">
      <div className="flex items-center justify-between">
        <Logo />
        <ThemeToggle />
      </div>
      <div className="flex flex-1 flex-col items-center justify-center py-24 text-center">
        <p className="caption-upper text-muted">404</p>
        <h1 className="display-lg mt-3 text-ink">Page not found</h1>
        <p className="mt-3 text-sm text-muted">The page you&apos;re looking for doesn&apos;t exist or has moved.</p>
        <Button href="/" className="mt-8">
          Back to Folio
        </Button>
      </div>
    </main>
  );
}
