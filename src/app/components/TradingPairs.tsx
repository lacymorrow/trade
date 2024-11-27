import {
  Box,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  Text,
} from "@chakra-ui/react";
import { useEffect, useState } from "react";

interface PairStats {
  symbol: string;
  price: number;
  change24h: number;
}

export default function TradingPairs() {
  const [pairs, setPairs] = useState<PairStats[]>([
    { symbol: "BTC/USD", price: 0, change24h: 0 },
    { symbol: "ETH/USD", price: 0, change24h: 0 },
    { symbol: "SOL/USD", price: 0, change24h: 0 },
  ]);

  useEffect(() => {
    const fetchPrices = async () => {
      // In a real implementation, this would fetch from your API
      // For now, we'll simulate price updates
      setPairs((prev) =>
        prev.map((pair) => ({
          ...pair,
          price:
            pair.price ||
            Math.random() * (pair.symbol.includes("BTC") ? 50000 : 3000),
          change24h: Math.random() * 10 - 5,
        }))
      );
    };

    fetchPrices();
    const interval = setInterval(fetchPrices, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Box p={6} borderRadius="lg" bg="white" shadow="base">
      <Text fontSize="lg" fontWeight="bold" mb={4}>
        Active Trading Pairs
      </Text>
      <SimpleGrid columns={3} spacing={4}>
        {pairs.map((pair) => (
          <Stat key={pair.symbol}>
            <StatLabel>{pair.symbol}</StatLabel>
            <StatNumber>
              $
              {pair.price.toLocaleString(undefined, {
                maximumFractionDigits: 2,
              })}
            </StatNumber>
            <Text color={pair.change24h >= 0 ? "green.500" : "red.500"}>
              {pair.change24h >= 0 ? "↑" : "↓"}{" "}
              {Math.abs(pair.change24h).toFixed(2)}%
            </Text>
          </Stat>
        ))}
      </SimpleGrid>
    </Box>
  );
}
