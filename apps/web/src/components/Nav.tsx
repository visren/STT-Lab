"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Compare" },
  { href: "/datasets", label: "Datasets" },
  { href: "/finetune", label: "Fine-tune" },
  { href: "/settings", label: "Settings" },
];

export function Nav() {
  const pathname = usePathname();
  return (
    <header className="mx-auto flex w-full max-w-6xl items-end justify-between gap-6 px-6 pb-2 pt-8">
      <Link href="/" className="group block">
        <p className="font-display text-4xl tracking-tight text-foam transition group-hover:text-white md:text-5xl">
          STT Lab
        </p>
      </Link>
      <nav className="mb-1 flex flex-wrap items-center gap-1 font-sans text-sm">
        {LINKS.map((link) => {
          const active =
            link.href === "/" ? pathname === "/" : pathname.startsWith(link.href);
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`rounded-md px-3 py-1.5 transition ${
                active
                  ? "bg-tide/20 text-foam"
                  : "text-mist hover:bg-ink-800/50 hover:text-foam"
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
