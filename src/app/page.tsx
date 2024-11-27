"use client";

import { useState } from "react";

export default function Home() {
  const [lastRun, setLastRun] = useState<string | null>(null);
  const [status, setStatus] = useState<"idle" | "running">("idle");
  const [error, setError] = useState<string | null>(null);

  const runBot = async () => {
    try {
      setStatus("running");
      setError(null);

      const response = await fetch("/api/trading", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${process.env.NEXT_PUBLIC_CRON_SECRET}`,
        },
      });

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.error || "Failed to run trading bot");
      }

      setLastRun(new Date().toLocaleString());
    } catch (err) {
      setError(err.message);
    } finally {
      setStatus("idle");
    }
  };

  return (
    <main className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Trading Bot Dashboard</h1>

        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div>
              <h2 className="text-sm text-gray-500">Status</h2>
              <p className="text-lg font-semibold">
                {status === "running" ? (
                  <span className="text-blue-500">Running</span>
                ) : (
                  <span className="text-green-500">Ready</span>
                )}
              </p>
            </div>
            <div>
              <h2 className="text-sm text-gray-500">Last Run</h2>
              <p className="text-lg font-semibold">{lastRun || "Never"}</p>
            </div>
          </div>

          <button
            onClick={runBot}
            disabled={status === "running"}
            className={`w-full py-2 px-4 rounded-md text-white font-medium ${
              status === "running"
                ? "bg-gray-400 cursor-not-allowed"
                : "bg-blue-500 hover:bg-blue-600"
            }`}
          >
            {status === "running" ? "Running..." : "Run Bot Now"}
          </button>

          {error && (
            <div className="mt-4 p-4 bg-red-50 text-red-700 rounded-md">
              {error}
            </div>
          )}
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Schedule</h2>
          <p className="text-gray-600">
            The bot runs automatically every 30 minutes during market hours:
          </p>
          <ul className="mt-2 space-y-2 text-gray-600">
            <li>• Monday - Friday</li>
            <li>• 9:30 AM - 4:00 PM ET</li>
            <li>• Every 30 minutes</li>
          </ul>
        </div>
      </div>
    </main>
  );
}
