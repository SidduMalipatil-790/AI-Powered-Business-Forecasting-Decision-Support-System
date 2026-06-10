import { useQuery } from "@tanstack/react-query";
import { Boxes, Tag, ShieldAlert, Lightbulb, ArrowRight } from "lucide-react";
import { getRecommendations, Recommendation } from "@/lib/api";
import { PageHeader } from "@/components/common/PageHeader";
import { ErrorState } from "@/components/common/ErrorState";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { cn } from "@/lib/utils";

const typeConfig = {
  inventory: { icon: Boxes, label: "Inventory", color: "from-primary/20 to-primary-glow/10 text-primary" },
  pricing: { icon: Tag, label: "Pricing", color: "from-accent/20 to-accent/5 text-accent" },
  risk: { icon: ShieldAlert, label: "Risk", color: "from-warning/20 to-warning/5 text-warning" },
};

const filters = [
  { id: "all", label: "All" },
  { id: "inventory", label: "Inventory" },
  { id: "pricing", label: "Pricing" },
  { id: "risk", label: "Risk" },
] as const;

export default function Decisions() {
  const [filter, setFilter] = useState<typeof filters[number]["id"]>("all");
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["recommendations"],
    queryFn: getRecommendations,
  });

  const filtered = data?.filter((r) => filter === "all" || r.type === filter) ?? [];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <PageHeader
        eyebrow="Decision Support"
        title="AI Recommendations"
        description="Actionable suggestions ranked by confidence and projected impact."
        actions={
          <div className="glass rounded-full p-1 flex items-center gap-1 flex-wrap">
            {filters.map((f) => (
              <Button
                key={f.id}
                size="sm"
                variant="ghost"
                onClick={() => setFilter(f.id)}
                className={`rounded-full h-8 px-3 text-xs font-semibold ${
                  filter === f.id ? "bg-gradient-primary text-primary-foreground" : ""
                }`}
              >
                {f.label}
              </Button>
            ))}
          </div>
        }
      />

      {isError ? (
        <ErrorState onRetry={() => refetch()} />
      ) : isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-44 rounded-2xl" />)}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map((r, i) => <RecommendationCard key={r.id} rec={r} index={i} />)}
        </div>
      )}
    </div>
  );
}

function RecommendationCard({ rec, index }: { rec: Recommendation; index: number }) {
  const cfg = typeConfig[rec.type];
  const Icon = cfg.icon;
  return (
    <div
      className="glass rounded-2xl p-5 hover:shadow-elevated hover:-translate-y-0.5 transition-all duration-300 animate-scale-in"
      style={{ animationDelay: `${index * 60}ms` }}
    >
      <div className="flex items-start gap-4">
        <div className={cn("h-11 w-11 rounded-xl bg-gradient-to-br flex items-center justify-center shrink-0", cfg.color)}>
          <Icon className="h-5 w-5" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[10px] uppercase tracking-wider font-semibold text-muted-foreground">{cfg.label}</span>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-success/10 text-success">{rec.confidence}% confidence</span>
          </div>
          <h3 className="font-display font-semibold text-base leading-snug">{rec.title}</h3>
          <p className="text-sm text-muted-foreground mt-2 leading-relaxed">{rec.explanation}</p>

          <div className="mt-4 h-1.5 rounded-full bg-muted overflow-hidden">
            <div
              className="h-full bg-gradient-primary rounded-full transition-all duration-700"
              style={{ width: `${rec.confidence}%` }}
            />
          </div>

          <div className="mt-4 flex items-center justify-between gap-3">
            <span className="text-xs font-semibold text-success flex items-center gap-1.5">
              <Lightbulb className="h-3.5 w-3.5" /> {rec.impact}
            </span>
            <Button size="sm" variant="ghost" className="rounded-full text-xs h-8">
              Apply <ArrowRight className="h-3 w-3 ml-1" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
