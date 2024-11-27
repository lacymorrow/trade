"use client";

import BotStatus from "@/components/BotStatus";
import PerformanceChart from "@/components/PerformanceChart";
import RecentTrades from "@/components/RecentTrades";
import TradingPairs from "@/components/TradingPairs";
import {
  Box,
  Button,
  Container,
  Grid,
  Heading,
  HStack,
  useToast,
} from "@chakra-ui/react";
import { useState } from "react";

export default function Home() {
  const [isRunning, setIsRunning] = useState(false);
  const [isTrading, setIsTrading] = useState(false);
  const toast = useToast();

  const handleStartStop = async () => {
    try {
      const response = await fetch("/api/bot/control", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ action: isRunning ? "stop" : "start" }),
      });

      if (!response.ok) throw new Error("Failed to control bot");

      setIsRunning(!isRunning);
      toast({
        title: `Bot ${isRunning ? "stopped" : "started"} successfully`,
        status: "success",
        duration: 3000,
      });
    } catch (error) {
      toast({
        title: "Error controlling bot",
        description: error.message,
        status: "error",
        duration: 5000,
      });
    }
  };

  const handleForceTrade = async () => {
    try {
      setIsTrading(true);
      const response = await fetch("/api/bot/trade", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) throw new Error("Failed to execute trade");

      const result = await response.json();
      toast({
        title: "Trade Analysis Complete",
        description: result.message,
        status: "success",
        duration: 5000,
      });
    } catch (error) {
      toast({
        title: "Error executing trade",
        description: error.message,
        status: "error",
        duration: 5000,
      });
    } finally {
      setIsTrading(false);
    }
  };

  return (
    <Container maxW="container.xl" py={8}>
      <Box mb={8}>
        <Heading mb={4}>Crypto Trading Bot Dashboard</Heading>
        <HStack spacing={4}>
          <Button
            colorScheme={isRunning ? "red" : "green"}
            onClick={handleStartStop}
            size="lg"
          >
            {isRunning ? "Stop Bot" : "Start Bot"}
          </Button>
          <Button
            colorScheme="blue"
            onClick={handleForceTrade}
            size="lg"
            isLoading={isTrading}
            loadingText="Analyzing"
            isDisabled={!isRunning}
          >
            Force Trade
          </Button>
        </HStack>
      </Box>

      <Grid templateColumns="repeat(2, 1fr)" gap={6} mb={8}>
        <BotStatus isRunning={isRunning} />
        <TradingPairs />
      </Grid>

      <Box mb={8}>
        <Heading size="md" mb={4}>
          Performance
        </Heading>
        <PerformanceChart />
      </Box>

      <Box>
        <Heading size="md" mb={4}>
          Recent Trades
        </Heading>
        <RecentTrades />
      </Box>
    </Container>
  );
}
