import "./globals.css";

import ThemeProvider from "@/components/providers/ThemeProvider";
import { GoogleOAuthProvider } from "@react-oauth/google";

export const metadata = {
  title: "Ganna Sahayak — Sugarcane Dept, Bihar",
  description: "AI assistant for sugarcane farmers — Sugarcane Industries Department, Government of Bihar.",
};

export const viewport = {
  width: "device-width",
  initialScale: 1,
};

// Fallback to the known client ID so Google Sign-in works even when
// NEXT_PUBLIC_GOOGLE_CLIENT_ID is not set in the deployment env vars.
const GOOGLE_CLIENT_ID =
  process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID ||
  "816946804113-j5fudgjc9m7o1aofism8bcd78997dps6.apps.googleusercontent.com";

export default function RootLayout({ children }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
          <ThemeProvider>
            {children}
          </ThemeProvider>
        </GoogleOAuthProvider>
      </body>
    </html>
  );
}
