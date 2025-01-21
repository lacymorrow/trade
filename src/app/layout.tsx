"use client";

import { Button } from "@/components/ui/button";
import { Inter } from "next/font/google";
import { usePathname, useRouter } from "next/navigation";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();

  const handleLogout = async () => {
    try {
      await fetch("/api/auth/logout", { method: "POST" });
      router.push("/login");
    } catch (error) {
      console.error("Logout error:", error);
    }
  };

  return (
    <html lang="en">
      <body className={inter.className}>
        {pathname !== "/login" && (
          <header className="p-4 bg-background border-b">
            <div className="container mx-auto flex justify-between items-center">
              <h1 className="text-xl font-bold">Trading Dashboard</h1>
              <Button variant="outline" onClick={handleLogout}>
                Logout
              </Button>
            </div>
          </header>
        )}
        {children}
      </body>
    </html>
  );
}
