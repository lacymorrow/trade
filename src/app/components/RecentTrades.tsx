import { Card } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";
import { useEffect, useState } from "react";

interface Trade {
  id: string;
  timestamp: string;
  symbol: string;
  type: "buy" | "sell";
  price: number;
  quantity: number;
  total: number;
}

export default function RecentTrades() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);

  useEffect(() => {
    const fetchTrades = async () => {
      try {
        setIsLoading(true);
        setError(null);
        setWarnings([]);

        const response = await fetch("/api/bot/trades");
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        // Check for error in response
        if (!data.success) {
          throw new Error(data.error?.message || "Failed to fetch trades");
        }

        // Store any warnings
        if (data.warnings) {
          setWarnings(
            data.warnings.map((w: any) => `${w.symbol}: ${w.message}`)
          );
        }

        // Transform the data to match our interface
        const formattedTrades: Trade[] = data.data.trades.map((trade: any) => ({
          id: trade.id,
          timestamp: new Date(trade.timestamp).toLocaleString(),
          symbol: trade.symbol,
          type: trade.side.toLowerCase(),
          price: trade.price,
          quantity: trade.quantity,
          total: trade.price * trade.quantity,
        }));

        setTrades(formattedTrades);
      } catch (err) {
        console.error("Error fetching trades:", err);
        setError(err instanceof Error ? err.message : "Failed to fetch trades");
      } finally {
        setIsLoading(false);
      }
    };

    fetchTrades();
    const interval = setInterval(fetchTrades, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, []);

  if (isLoading) {
    return <div>Loading trades...</div>;
  }

  if (error) {
    return <div className="text-red-500">Error: {error}</div>;
  }

  return (
    <Card className="p-6 overflow-x-auto">
      {warnings.length > 0 && (
        <div className="mb-4">
          {warnings.map((warning, index) => (
            <div key={index} className="text-yellow-600 text-sm">
              Warning: {warning}
            </div>
          ))}
        </div>
      )}
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Time</TableHead>
            <TableHead>Symbol</TableHead>
            <TableHead>Type</TableHead>
            <TableHead className="text-right">Price</TableHead>
            <TableHead className="text-right">Quantity</TableHead>
            <TableHead className="text-right">Total</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {trades.length === 0 ? (
            <TableRow>
              <TableCell colSpan={6} className="text-center">
                No trades found
              </TableCell>
            </TableRow>
          ) : (
            trades.map((trade) => (
              <TableRow key={trade.id}>
                <TableCell>{trade.timestamp}</TableCell>
                <TableCell>{trade.symbol}</TableCell>
                <TableCell>
                  <span
                    className={cn(
                      "font-medium",
                      trade.type === "buy" ? "text-green-600" : "text-red-600"
                    )}
                  >
                    {trade.type.toUpperCase()}
                  </span>
                </TableCell>
                <TableCell className="text-right">
                  $
                  {trade.price.toLocaleString(undefined, {
                    maximumFractionDigits: 2,
                  })}
                </TableCell>
                <TableCell className="text-right">
                  {trade.quantity.toFixed(8)}
                </TableCell>
                <TableCell className="text-right">
                  $
                  {trade.total.toLocaleString(undefined, {
                    maximumFractionDigits: 2,
                  })}
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </Card>
  );
}
