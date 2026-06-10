import { LucideIcon, ArrowUpRight, ArrowDownRight } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

interface KpiCardProps {
  label: string;
  value: string;
  delta?: number;
  icon: LucideIcon;
  accent?: "primary" | "accent" | "success" | "warning";
  loading?: boolean;
}

const accents = {
  primary: "from-primary/20 to-primary-glow/10 text-primary",
  accent: "from-accent/20 to-accent/5 text-accent",
  success: "from-success/20 to-success/5 text-success",
  warning: "from-warning/20 to-warning/5 text-warning",
};

export function KpiCard({ label, value, delta, icon: Icon, accent = "primary", loading }: KpiCardProps) {
  if (loading) {
    return (
      <div className="glass rounded-2xl p-5">
        <Skeleton className="h-4 w-24 mb-4" />
        <Skeleton className="h-8 w-32 mb-2" />
        <Skeleton className="h-3 w-16" />
      </div>
    );
  }
  const positive = (delta ?? 0) >= 0;
  return (
    <div className="glass rounded-2xl p-5 hover:shadow-elevated transition-all duration-300 hover:-translate-y-0.5 group animate-scale-in">
      <div className="flex items-start justify-between mb-4">
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{label}</span>
        <div className={cn("h-9 w-9 rounded-xl bg-gradient-to-br flex items-center justify-center group-hover:scale-110 transition-transform", accents[accent])}>
          <Icon className="h-4 w-4" />
        </div>
      </div>
      <div className="text-2xl md:text-3xl font-display font-bold tracking-tight">{value}</div>
      {delta !== undefined && (
        <div className={cn("mt-2 inline-flex items-center gap-1 text-xs font-semibold rounded-full px-2 py-0.5",
          positive ? "text-success bg-success/10" : "text-danger bg-danger/10")}>
          {positive ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
          {Math.abs(delta)}%
          <span className="text-muted-foreground font-normal ml-1">vs last week</span>
        </div>
      )}
    </div>
  );
}
