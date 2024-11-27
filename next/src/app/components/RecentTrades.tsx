import { Box, Table, Tbody, Td, Text, Th, Thead, Tr } from "@chakra-ui/react";
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
    <Box p={6} borderRadius="lg" bg="white" shadow="base" overflowX="auto">
      <Table variant="simple">
        <Thead>
          <Tr>
            <Th>Time</Th>
            <Th>Symbol</Th>
            <Th>Type</Th>
            <Th isNumeric>Price</Th>
            <Th isNumeric>Quantity</Th>
            <Th isNumeric>Total</Th>
          </Tr>
        </Thead>
        <Tbody>
          {trades.map((trade) => (
            <Tr key={trade.id}>
              <Td>{trade.timestamp}</Td>
              <Td>{trade.symbol}</Td>
              <Td>
                <Text color={trade.type === "buy" ? "green.500" : "red.500"}>
                  {trade.type.toUpperCase()}
                </Text>
              </Td>
              <Td isNumeric>
                $
                {trade.price.toLocaleString(undefined, {
                  maximumFractionDigits: 2,
                })}
              </Td>
              <Td isNumeric>{trade.quantity.toFixed(8)}</Td>
              <Td isNumeric>
                $
                {trade.total.toLocaleString(undefined, {
                  maximumFractionDigits: 2,
                })}
              </Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
    </Box>
  );
}
