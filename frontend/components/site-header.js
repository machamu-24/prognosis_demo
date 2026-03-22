import Link from "next/link";

export function SiteHeader() {
  return (
    <header className="site-header">
      <div className="shell site-header__inner">
        <Link className="brand" href="/">
          Prognosis AI Demo
        </Link>
        <nav className="site-nav">
          <Link href="/demo">Demo</Link>
          <Link href="/validation">Validation</Link>
        </nav>
      </div>
    </header>
  );
}

