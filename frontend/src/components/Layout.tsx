import type { ReactNode } from "react";

interface LayoutProps {
  sidebar: ReactNode;
  children: ReactNode;
}

export function Layout({ sidebar, children }: LayoutProps) {
  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">// karamfrm.com / quant tools</p>
          <h1>Credit Risk Engine</h1>
        </div>
        <nav className="topbar-nav">
          <a href="/">Home</a>
          <a href="/corr">CORR</a>
          <a href="/tail-risk">Tail Risk</a>
          <span className="topbar-active">Credit</span>
        </nav>
      </header>

      <div className="workspace">
        <aside className="sidebar">{sidebar}</aside>
        <main className="main-content">{children}</main>
      </div>
    </div>
  );
}
