import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Area, AreaChart, CartesianGrid, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Download, Sparkles, TrendingUp } from "lucide-react";
import { postForecast, ForecastResponse } from "@/lib/api";
import { PageHeader } from "@/components/common/PageHeader";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";

const products = ["All Products", "Wireless Earbuds Pro", "Smart Watch X", "Coffee Beans 1kg", "Winter Coat", "Yoga Mat"];
const horizons = [7, 30, 90];

const tooltipStyle = {
  backgroundColor: "hsl(var(--popover))",
  border: "1px solid hsl(var(--border))",
  borderRadius: "12px",
  fontSize: "12px",
};

export default function Forecasting() {
  const [horizon, setHorizon] = useState(30);
  const [product, setProduct] = useState(products[0]);
  const [data, setData] = useState<ForecastResponse | null>(null);

  const mutation = useMutation({
    mutationFn: postForecast,
    onSuccess: (d) => {
      setData(d);
      toast.success("Forecast generated", { description: `${d.points.length}-day horizon for ${d.product}` });
    },
    onError: () => toast.error("Forecast failed", { description: "Please try again." }),
  });

  const run = () => mutation.mutate({ horizon, product });

  const download = () => {
    if (!data) return;
    const csv = ["date,forecast,lower,upper", ...data.points.map((p) => `${p.date},${p.forecast},${p.lower},${p.upper}`)].join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `forecast_${product}_${horizon}d.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <PageHeader
        eyebrow="Forecasting"
        title="Predictive Engine"
        description="Generate AI forecasts with confidence intervals across product lines and horizons."
      />

      <div className="glass rounded-2xl p-5 grid grid-cols-1 md:grid-cols-12 gap-4 items-end animate-scale-in">
        <div className="md:col-span-4 space-y-2">
          <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Forecast horizon</label>
          <div className="glass rounded-full p-1 inline-flex w-full">
            {horizons.map((h) => (
              <button
                key={h}
                onClick={() => setHorizon(h)}
                className={`flex-1 h-9 rounded-full text-sm font-semibold transition-all ${
                  horizon === h ? "bg-gradient-primary text-primary-foreground shadow-elevated" : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {h} days
              </button>
            ))}
          </div>
        </div>
        <div className="md:col-span-5 space-y-2">
          <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Product / Store</label>
          <Select value={product} onValueChange={setProduct}>
            <SelectTrigger className="glass rounded-xl h-11 border-border/50"><SelectValue /></SelectTrigger>
            <SelectContent className="glass-strong">
              {products.map((p) => <SelectItem key={p} value={p}>{p}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>
        <div className="md:col-span-3 flex gap-2">
          <Button onClick={run} disabled={mutation.isPending} className="flex-1 h-11 rounded-xl bg-gradient-primary hover:opacity-90 shadow-elevated">
            <Sparkles className="h-4 w-4 mr-2" />
            {mutation.isPending ? "Generating…" : "Run Forecast"}
          </Button>
        </div>
      </div>

      {mutation.isPending && <Skeleton className="h-96 w-full rounded-2xl" />}

      {data && !mutation.isPending && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { label: "Mean", value: `$${data.summary.mean.toLocaleString()}` },
              { label: "Min", value: `$${data.summary.min.toLocaleString()}` },
              { label: "Max", value: `$${data.summary.max.toLocaleString()}` },
              { label: "MAPE", value: `${data.summary.mape}%` },
            ].map((s) => (
              <div key={s.label} className="glass rounded-2xl p-4 animate-fade-in">
                <div className="text-xs text-muted-foreground uppercase tracking-wider">{s.label}</div>
                <div className="text-xl font-display font-bold mt-1">{s.value}</div>
              </div>
            ))}
          </div>

          <div className="glass rounded-2xl p-5 animate-fade-in">
            <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
              <div>
                <h3 className="font-display font-semibold text-lg flex items-center gap-2"><TrendingUp className="h-4 w-4 text-primary" /> {product} — {horizon}d forecast</h3>
                <p className="text-xs text-muted-foreground">Shaded band = 95% confidence interval</p>
              </div>
              <Button onClick={download} variant="outline" className="rounded-full">
                <Download className="h-4 w-4 mr-2" /> Download CSV
              </Button>
            </div>
            <ResponsiveContainer width="100%" height={380}>
              <AreaChart data={data.points}>
                <defs>
                  <linearGradient id="ciGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity={0.25} />
                    <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                <XAxis dataKey="date" stroke="hsl(var(--muted-foreground))" fontSize={11} tickFormatter={(v) => v.slice(5)} />
                <YAxis stroke="hsl(var(--muted-foreground))" fontSize={11} tickFormatter={(v) => `$${(v / 1000).toFixed(0)}k`} />
                <Tooltip contentStyle={tooltipStyle} />
                <Area type="monotone" dataKey="upper" stroke="transparent" fill="url(#ciGrad)" />
                <Area type="monotone" dataKey="lower" stroke="transparent" fill="hsl(var(--background))" />
                <Line type="monotone" dataKey="forecast" stroke="hsl(var(--primary))" strokeWidth={3} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </>
      )}

      {!data && !mutation.isPending && (
        <div className="glass rounded-2xl p-12 text-center animate-fade-in">
          <div className="mx-auto h-16 w-16 rounded-2xl bg-gradient-primary flex items-center justify-center mb-4 animate-float shadow-elevated">
            <Sparkles className="h-8 w-8 text-primary-foreground" />
          </div>
          <h3 className="font-display font-semibold text-lg mb-1">Ready to forecast</h3>
          <p className="text-sm text-muted-foreground">Choose a horizon & product, then run the AI engine.</p>
        </div>
      )}
    </div>
  );
}
