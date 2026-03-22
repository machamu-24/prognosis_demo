import "./globals.css";

import { SiteHeader } from "../components/site-header";


export const metadata = {
  title: "Prognosis AI Demo",
  description: "AI-driven prognosis prediction demo for FAC 0-3 patients."
};


export default function RootLayout({ children }) {
  return (
    <html lang="ja">
      <body>
        <SiteHeader />
        {children}
      </body>
    </html>
  );
}

