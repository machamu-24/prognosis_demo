"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function SiteHeader() {
  const pathname = usePathname();

  const navItems = [
    { href: "/demo", label: "予測デモ" },
    { href: "/validation", label: "モデル検証" },
  ];

  return (
    <header className="site-header">
      <div className="shell site-header__inner">
        <Link className="brand" href="/">
          Prognosis AI
        </Link>
        <nav className="site-nav">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={pathname === item.href ? "nav-active" : ""}
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
