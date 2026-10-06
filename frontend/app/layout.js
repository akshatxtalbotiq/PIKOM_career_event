import "./globals.css";

export const metadata = {
  title: "PIKOM Career Festival",
  description: "Explore employers, sessions and opportunities at your event.",
};

export default function RootLayout({ children }) {
  return <html lang="en"><body>{children}</body></html>;
}
