"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const links = [
  { href: "/", label: "Compare" },
  { href: "/datasets", label: "Datasets" },
  { href: "/adapt", label: "Adapt" },
  { href: "/settings", label: "Settings" },
];

export function Nav() {
  const pathname = usePathname();

  return (
    <header className="mx-auto flex w-full max-w-6xl items-end justify-between gap-6 px-6 pb-2 pt-8">
      <Link href="/" className="group">
        <div className="font-[family-name:var(--font-display)] text-3xl font-bold tracking-tight text-[var(--accent)] transition-transform duration-300 group-hover:-translate-y-0.5 md:text-4xl">
          STT Lab
        </div>
        <p className="mt-1 text-sm text-[var(--muted)]">Compare models. Adapt to your voice.</p>
      </Link>
      <nav className="flex flex-wrap items-center gap-1 text-sm">
        {links.map((link) => {
          const active =
            link.href === "/" ? pathname === "/" : pathname.startsWith(link.href);
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`rounded-md px-3 py-2 transition-colors ${
                active
                  ? "bg-[var(--accent)] text-[var(--ink)]"
                  : "text-[var(--muted)] hover:text-[var(--text)]"
              }`}
            >
              {link.label}
            </Link>
          );
        })}
      </nav>
    </header>
  );
}
