import {
  Box,
  Stat,
  StatGroup,
  StatLabel,
  StatNumber,
  Text,
} from "@chakra-ui/react";
import { useEffect, useState } from "react";

interface BotStatusProps {
  isRunning: boolean;
}

export default function BotStatus({ isRunning }: BotStatusProps) {
  const [stats, setStats] = useState({
    uptime: "0:00:00",
    totalTrades: 0,
    profitLoss: 0,
  });

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch("/api/bot/stats");
        if (response.ok) {
          const data = await response.json();
          setStats(data);
        }
      } catch (error) {
        console.error("Failed to fetch bot stats:", error);
      }
    };

    if (isRunning) {
      fetchStats();
      const interval = setInterval(fetchStats, 30000); // Update every 30 seconds
      return () => clearInterval(interval);
    }
  }, [isRunning]);

  return (
    <Box p={6} borderRadius="lg" bg="white" shadow="base">
      <Text fontSize="lg" fontWeight="bold" mb={4}>
        Bot Status
      </Text>
      <StatGroup>
        <Stat>
          <StatLabel>Status</StatLabel>
          <StatNumber>
            <Text color={isRunning ? "green.500" : "red.500"}>
              {isRunning ? "Running" : "Stopped"}
            </Text>
          </StatNumber>
        </Stat>
        <Stat>
          <StatLabel>Uptime</StatLabel>
          <StatNumber>{stats.uptime}</StatNumber>
        </Stat>
        <Stat>
          <StatLabel>Total Trades</StatLabel>
          <StatNumber>{stats.totalTrades}</StatNumber>
        </Stat>
        <Stat>
          <StatLabel>P/L</StatLabel>
          <StatNumber color={stats.profitLoss >= 0 ? "green.500" : "red.500"}>
            ${stats.profitLoss.toFixed(2)}
          </StatNumber>
        </Stat>
      </StatGroup>
    </Box>
  );
}
