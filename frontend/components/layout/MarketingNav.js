import Link from "next/link";
import Button from "@/components/ui/Button";
import Logo from "@/components/ui/Logo";
import ThemeToggle from "@/components/ui/ThemeToggle";

const LINKS = [
  { href: "/#how", label: "How it works" },
  { href: "/#product", label: "Product" },
  { href: "/#privacy", label: "Privacy" },
  { href: "/#faq", label: "FAQ" },
];

export default function MarketingNav() {
  return (
    <header className="sticky top-0 z-10 border-b border-hairline/60 bg-canvas/90 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-[1200px] items-center justify-between gap-4 px-6">
        <Logo />
        <nav className="hidden items-center gap-6 text-[15px] text-muted lg:flex" aria-label="Product">
          {LINKS.map((link) => (
            <Link key={link.href} href={link.href} className="transition-colors hover:text-ink">
              {link.label}
            </Link>
          ))}
        </nav>
        <div className="flex items-center gap-1">
          <ThemeToggle />
          <Button variant="ghost" href="/signin">
            Sign in
          </Button>
          <Button href="/signup">Get started</Button>
        </div>
      </div>
    </header>
  );
}

export function Footer() {
  return (
    <footer className="border-t border-hairline">
      <div className="mx-auto grid max-w-[1200px] gap-10 px-6 py-16 sm:grid-cols-2 lg:grid-cols-4">
        <div className="sm:col-span-2">
          <Logo />
          <p className="mt-4 max-w-sm text-[15px] leading-relaxed text-body">
            Your documents, your key, answers you can verify. Folio is a private RAG workspace: upload files, connect a
            Hugging Face token, and chat with citations.
          </p>
        </div>
        <div>
          <p className="caption-upper text-muted">Product</p>
          <ul className="mt-4 space-y-2 text-[15px] text-body">
            <li>
              <Link href="/#how" className="hover:text-ink">
                How it works
              </Link>
            </li>
            <li>
              <Link href="/#product" className="hover:text-ink">
                What you get
              </Link>
            </li>
            <li>
              <Link href="/#privacy" className="hover:text-ink">
                Privacy
              </Link>
            </li>
            <li>
              <Link href="/#faq" className="hover:text-ink">
                FAQ
              </Link>
            </li>
          </ul>
        </div>
        <div>
          <p className="caption-upper text-muted">Account</p>
          <ul className="mt-4 space-y-2 text-[15px] text-body">
            <li>
              <Link href="/signup" className="hover:text-ink">
                Create an account
              </Link>
            </li>
            <li>
              <Link href="/signin" className="hover:text-ink">
                Sign in
              </Link>
            </li>
          </ul>
        </div>
      </div>
    </footer>
  );
}
