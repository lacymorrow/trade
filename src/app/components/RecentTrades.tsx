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

  useEffect(() => {
    // In a real implementation, this would fetch from your API
    // For now, we'll generate sample data
    const generateTrades = () => {
      const symbols = ["BTC/USD", "ETH/USD", "SOL/USD"];
      const newTrades: Trade[] = Array.from({ length: 5 }, (_, i) => ({
        id: `trade-${Date.now()}-${i}`,
        timestamp: new Date(Date.now() - i * 3600000).toLocaleString(),
        symbol: symbols[Math.floor(Math.random() * symbols.length)],
        type: Math.random() > 0.5 ? "buy" : "sell",
        price: Math.random() * 50000,
        quantity: Math.random() * 2,
        total: 0,
      }));

      // Calculate totals
      newTrades.forEach((trade) => {
        trade.total = trade.price * trade.quantity;
      });

      setTrades(newTrades);
    };

    generateTrades();
    const interval = setInterval(generateTrades, 60000); // Update every minute
    return () => clearInterval(interval);
  }, []);

  return (
    <Card className="p-6 overflow-x-auto">
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
          {trades.map((trade) => (
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
          ))}
        </TableBody>
      </Table>
    </Card>
  );
}
