import { useQuery } from "@tanstack/react-query";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { DollarSign, TrendingUp, Activity, Bell, Calendar } from "lucide-react";
import { getDashboard } from "@/lib/api";
import { KpiCard } from "@/components/dashboard/KpiCard";
import { PageHeader } from "@/components/common/PageHeader";
import { ErrorState } from "@/components/common/ErrorState";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { useState } from "react";

const ranges = [
  { label: "7D", days: 7 },
  { label: "30D", days: 30 },
  { label: "90D", days: 90 },
];

const tooltipStyle = {
  backgroundColor: "hsl(var(--popover))",
  border: "1px solid hsl(var(--border))",
  borderRadius: "12px",
  fontSize: "12px",
  boxShadow: "var(--shadow-glass)",
};

export default function Dashboard() {
  const [range, setRange] = useState(30);
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["dashboard"],
    queryFn: getDashboard,
  });

  const series = data?.series.slice(-(range + 7)) ?? [];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <PageHeader
        eyebrow="Overview"
        title="Business Pulse"
        description="Real-time AI-driven insights across sales, demand and operational signals."
        actions={
          <div className="glass rounded-full p-1 flex items-center gap-1">
            <Calendar className="h-4 w-4 ml-2 text-muted-foreground" />
            {ranges.map((r) => (
              <Button
                key={r.label}
                size="sm"
                variant="ghost"
                onClick={() => setRange(r.days)}
                className={`rounded-full h-8 px-3 text-xs font-semibold ${
                  range === r.days ? "bg-gradient-primary text-primary-foreground" : ""
                }`}
              >
                {r.label}
              </Button>
            ))}
          </div>
        }
      />

      {isError ? (
        <ErrorState onRetry={() => refetch()} />
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <KpiCard label="Total Sales" value={data ? `$${data.totalSales.toLocaleString()}` : ""} delta={8.2} icon={DollarSign} accent="primary" loading={isLoading} />
            <KpiCard label="Predicted (7d)" value={data ? `$${data.predictedSales.toLocaleString()}` : ""} delta={12.4} icon={TrendingUp} accent="accent" loading={isLoading} />
            <KpiCard label="Growth" value={data ? `${data.growth}%` : ""} delta={3.1} icon={Activity} accent="success" loading={isLoading} />
            <KpiCard label="Active Alerts" value={data ? `${data.alerts}` : ""} delta={-25} icon={Bell} accent="warning" loading={isLoading} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="glass rounded-2xl p-5 lg:col-span-2 animate-fade-in">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="font-display font-semibold text-lg">Sales — Historical vs Predicted</h3>
                  <p className="text-xs text-muted-foreground">Forecast confidence: 94%</p>
                </div>
                <div className="hidden sm:flex items-center gap-3 text-xs">
                  <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-primary" /> Actual</span>
                  <span className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-accent" /> Predicted</span>
                </div>
              </div>
              {isLoading ? (
                <Skeleton className="h-72 w-full rounded-xl" />
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={series}>
                    <defs>
                      <linearGradient id="actualGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity={0.4} />
                        <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="predGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="hsl(var(--accent))" stopOpacity={0.4} />
                        <stop offset="100%" stopColor="hsl(var(--accent))" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                    <XAxis dataKey="date" stroke="hsl(var(--muted-foreground))" fontSize={11} tickFormatter={(v) => v.slice(5)} />
                    <YAxis stroke="hsl(var(--muted-foreground))" fontSize={11} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                    <Tooltip contentStyle={tooltipStyle} />
                    <Area type="monotone" dataKey="actual" stroke="hsl(var(--primary))" strokeWidth={2.5} fill="url(#actualGrad)" />
                    <Area type="monotone" dataKey="predicted" stroke="hsl(var(--accent))" strokeWidth={2.5} strokeDasharray="6 4" fill="url(#predGrad)" />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </div>

            <div className="glass rounded-2xl p-5 animate-fade-in">
              <div className="mb-4">
                <h3 className="font-display font-semibold text-lg">Category Performance</h3>
                <p className="text-xs text-muted-foreground">Sales vs target</p>
              </div>
              {isLoading ? (
                <Skeleton className="h-72 w-full rounded-xl" />
              ) : (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={data?.categories} layout="vertical" margin={{ left: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" horizontal={false} />
                    <XAxis type="number" stroke="hsl(var(--muted-foreground))" fontSize={11} tickFormatter={(v) => `${v / 1000}k`} />
                    <YAxis type="category" dataKey="category" stroke="hsl(var(--muted-foreground))" fontSize={11} width={70} />
                    <Tooltip contentStyle={tooltipStyle} />
                    <Bar dataKey="target" fill="hsl(var(--muted))" radius={[0, 6, 6, 0]} />
                    <Bar dataKey="sales" fill="hsl(var(--primary))" radius={[0, 6, 6, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          <div className="glass rounded-2xl p-5 animate-fade-in">
            <div className="mb-4">
              <h3 className="font-display font-semibold text-lg">Daily Momentum</h3>
              <p className="text-xs text-muted-foreground">Combined actual + predicted trajectory</p>
            </div>
            {isLoading ? (
              <Skeleton className="h-48 w-full rounded-xl" />
            ) : (
              <ResponsiveContainer width="100%" height={180}>
                <LineChart data={series}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                  <XAxis dataKey="date" stroke="hsl(var(--muted-foreground))" fontSize={11} tickFormatter={(v) => v.slice(5)} />
                  <YAxis hide />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Line type="monotone" dataKey="actual" stroke="hsl(var(--primary))" strokeWidth={2} dot={false} />
                  <Line type="monotone" dataKey="predicted" stroke="hsl(var(--accent))" strokeWidth={2} strokeDasharray="5 4" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </>
      )}
    </div>
  );
}
