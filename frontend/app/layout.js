import "./globals.css";

import { SiteHeader } from "../components/site-header";


export const metadata = {
  title: "歩行予後予測 AI — Prognosis AI",
  description: "FAC 0-3 の患者を対象とした、説明可能な歩行予後予測デモ"
};


export default function RootLayout({ children }) {
  return (
    <html lang="ja">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body>
        <SiteHeader />
        {children}
      </body>
    </html>
  );
}
