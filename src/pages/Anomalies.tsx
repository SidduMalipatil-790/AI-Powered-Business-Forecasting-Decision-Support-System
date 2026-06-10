import { useQuery } from "@tanstack/react-query";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { AlertTriangle, ArrowDown, ArrowUp } from "lucide-react";
import { getAnomalies, Anomaly } from "@/lib/api";
import { PageHeader } from "@/components/common/PageHeader";
import { ErrorState } from "@/components/common/ErrorState";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

const sevConfig = {
  low: { label: "Low", color: "bg-success/15 text-success border-success/30", bar: "hsl(var(--success))" },
  medium: { label: "Medium", color: "bg-warning/15 text-warning border-warning/30", bar: "hsl(var(--warning))" },
  high: { label: "High", color: "bg-danger/15 text-danger border-danger/30", bar: "hsl(var(--danger))" },
};

const tooltipStyle = {
  backgroundColor: "hsl(var(--popover))",
  border: "1px solid hsl(var(--border))",
  borderRadius: "12px",
  fontSize: "12px",
};

export default function Anomalies() {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["anomalies"],
    queryFn: getAnomalies,
  });

  const chartData = (data ?? []).map((a) => ({ ...a, abs: Math.abs(a.delta) })).sort((a, b) => a.date.localeCompare(b.date));
  const counts = (sev: Anomaly["severity"]) => (data ?? []).filter((a) => a.severity === sev).length;

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <PageHeader
        eyebrow="Anomaly Detection"
        title="Signal & Noise"
        description="Statistical outliers detected across key business metrics over the last 14 days."
      />

      {isError ? (
        <ErrorState onRetry={() => refetch()} />
      ) : (
        <>
          <div className="grid grid-cols-3 gap-4">
            {(["high", "medium", "low"] as const).map((s) => (
              <div key={s} className="glass rounded-2xl p-5 animate-scale-in">
                <div className={cn("inline-flex text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border", sevConfig[s].color)}>
                  {sevConfig[s].label}
                </div>
                <div className="text-3xl font-display font-bold mt-3">{isLoading ? "—" : counts(s)}</div>
                <div className="text-xs text-muted-foreground mt-1">flagged events</div>
              </div>
            ))}
          </div>

          <div className="glass rounded-2xl p-5 animate-fade-in">
            <h3 className="font-display font-semibold text-lg mb-1">Anomaly Timeline</h3>
            <p className="text-xs text-muted-foreground mb-4">Magnitude of deviation by date</p>
            {isLoading ? (
              <Skeleton className="h-64 w-full rounded-xl" />
            ) : (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                  <XAxis dataKey="date" stroke="hsl(var(--muted-foreground))" fontSize={11} tickFormatter={(v) => v.slice(5)} />
                  <YAxis stroke="hsl(var(--muted-foreground))" fontSize={11} tickFormatter={(v) => `${v}%`} />
                  <Tooltip contentStyle={tooltipStyle} />
                  <Bar dataKey="abs" radius={[8, 8, 0, 0]}>
                    {chartData.map((d, i) => (
                      <Cell key={i} fill={sevConfig[d.severity].bar} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>

          <div className="glass rounded-2xl p-5 animate-fade-in">
            <h3 className="font-display font-semibold text-lg mb-4">Flagged Events</h3>
            {isLoading ? (
              <div className="space-y-3">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-20 rounded-xl" />)}</div>
            ) : (
              <ul className="space-y-3">
                {(data ?? []).map((a, i) => {
                  const positive = a.delta > 0;
                  return (
                    <li
                      key={a.id}
                      className="flex items-start gap-4 p-4 rounded-xl bg-secondary/40 hover:bg-secondary transition-all animate-slide-up"
                      style={{ animationDelay: `${i * 50}ms` }}
                    >
                      <div className={cn("h-10 w-10 rounded-xl flex items-center justify-center shrink-0", sevConfig[a.severity].color, "border")}>
                        <AlertTriangle className="h-4 w-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h4 className="font-semibold">{a.metric}</h4>
                          <span className={cn("text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border", sevConfig[a.severity].color)}>
                            {sevConfig[a.severity].label}
                          </span>
                          <span className="text-xs text-muted-foreground">{a.date}</span>
                        </div>
                        <p className="text-sm text-muted-foreground mt-1">{a.description}</p>
                      </div>
                      <div className={cn("flex items-center gap-1 font-bold text-lg shrink-0", positive ? "text-success" : "text-danger")}>
                        {positive ? <ArrowUp className="h-4 w-4" /> : <ArrowDown className="h-4 w-4" />}
                        {Math.abs(a.delta)}%
                      </div>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        </>
      )}
    </div>
  );
}
