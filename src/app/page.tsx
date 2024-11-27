"use client";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "@/hooks/use-toast";
import { AlertCircle, CheckCircle2, PlayCircle } from "lucide-react";
import { useState } from "react";
import RecentTrades from "./components/RecentTrades";

export default function Home() {
  const [botStatus, setBotStatus] = useState<"running" | "stopped">("stopped");
  const [lastRun, setLastRun] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleRunBot = async () => {
    try {
      setIsLoading(true);
      setBotStatus("running");

      const response = await fetch("/api/trading", {
        method: "POST",
        headers: {
          Authorization: "Bearer development-secret",
          "Content-Type": "application/json",
        },
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Failed to run trading bot");
      }

      setLastRun(new Date().toLocaleString());
      toast({
        title: "Success",
        description: "Trading bot analysis completed successfully",
      });
    } catch (error) {
      console.error("Error running bot:", error);
      toast({
        variant: "destructive",
        title: "Error",
        description:
          error instanceof Error ? error.message : "Failed to run trading bot",
      });
    } finally {
      setIsLoading(false);
      setBotStatus("stopped");
    }
  };

  return (
    <main className="container mx-auto p-4">
      <div className="flex flex-col gap-6">
        {/* Header */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold">Trading Bot Dashboard</h1>
            <p className="text-muted-foreground">
              Monitor and control your automated trading strategy
            </p>
          </div>
          <Badge variant={botStatus === "running" ? "default" : "secondary"}>
            {botStatus === "running" ? "Bot Running" : "Bot Stopped"}
          </Badge>
        </div>

        {/* Status Cards */}
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader>
              <CardTitle>Bot Status</CardTitle>
              <CardDescription>Current operational status</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                {botStatus === "running" ? (
                  <CheckCircle2 className="h-5 w-5 text-green-500" />
                ) : (
                  <AlertCircle className="h-5 w-5 text-yellow-500" />
                )}
                <span className="font-medium">
                  {botStatus === "running" ? "Active" : "Inactive"}
                </span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Last Run</CardTitle>
              <CardDescription>Most recent execution</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="font-medium">{lastRun || "Never"}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Controls</CardTitle>
              <CardDescription>Manage bot operations</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2">
                <Button
                  onClick={handleRunBot}
                  variant="default"
                  className="w-full"
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <>
                      <span className="animate-spin mr-2">⚪</span>
                      Running...
                    </>
                  ) : (
                    <>
                      <PlayCircle className="mr-2 h-4 w-4" />
                      Run Analysis
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <Tabs defaultValue="trades" className="w-full">
          <TabsList>
            <TabsTrigger value="trades">Recent Trades</TabsTrigger>
            <TabsTrigger value="analysis">Analysis</TabsTrigger>
            <TabsTrigger value="settings">Settings</TabsTrigger>
          </TabsList>
          <TabsContent value="trades">
            <Card>
              <CardHeader>
                <CardTitle>Recent Trades</CardTitle>
                <CardDescription>Latest trading activity</CardDescription>
              </CardHeader>
              <CardContent>
                <RecentTrades />
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="analysis">
            <Card>
              <CardHeader>
                <CardTitle>Market Analysis</CardTitle>
                <CardDescription>
                  Technical and sentiment indicators
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>Analysis Module</AlertTitle>
                  <AlertDescription>
                    Market analysis data will be displayed here.
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="settings">
            <Card>
              <CardHeader>
                <CardTitle>Bot Settings</CardTitle>
                <CardDescription>Configure trading parameters</CardDescription>
              </CardHeader>
              <CardContent>
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>Settings Module</AlertTitle>
                  <AlertDescription>
                    Trading bot settings will be configured here.
                  </AlertDescription>
                </Alert>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </main>
  );
}
