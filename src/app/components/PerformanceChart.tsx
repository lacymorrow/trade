import { Box } from "@chakra-ui/react";
import {
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Title,
  Tooltip,
} from "chart.js";
import { useEffect, useState } from "react";
import { Line } from "react-chartjs-2";

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface PerformanceData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    borderColor: string;
    backgroundColor: string;
  }[];
}

export default function PerformanceChart() {
  const [data, setData] = useState<PerformanceData>({
    labels: [],
    datasets: [
      {
        label: "Portfolio Value ($)",
        data: [],
        borderColor: "rgb(75, 192, 192)",
        backgroundColor: "rgba(75, 192, 192, 0.5)",
      },
    ],
  });

  useEffect(() => {
    // In a real implementation, this would fetch from your API
    // For now, we'll generate sample data
    const generateData = () => {
      const labels = Array.from({ length: 24 }, (_, i) => {
        const d = new Date();
        d.setHours(d.getHours() - (23 - i));
        return d.toLocaleTimeString();
      });

      let value = 10000; // Starting value
      const values = Array.from({ length: 24 }, () => {
        value = value * (1 + (Math.random() * 0.02 - 0.01)); // ±1% change
        return value;
      });

      setData({
        labels,
        datasets: [
          {
            ...data.datasets[0],
            data: values,
          },
        ],
      });
    };

    generateData();
    const interval = setInterval(generateData, 60000); // Update every minute
    return () => clearInterval(interval);
  }, []);

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: "top" as const,
      },
      title: {
        display: false,
      },
    },
    scales: {
      y: {
        beginAtZero: false,
      },
    },
  };

  return (
    <Box p={6} borderRadius="lg" bg="white" shadow="base">
      <Line options={options} data={data} />
    </Box>
  );
}
