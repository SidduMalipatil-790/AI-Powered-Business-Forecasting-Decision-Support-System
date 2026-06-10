import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Brain, Settings2, Loader2, ArrowRight } from "lucide-react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { postSimulate } from "@/lib/api";

const PRODUCTS = [
  { id: "ALL", name: "All Products" },
  { id: "P001", name: "Wireless Earbuds Pro" },
  { id: "P002", name: "Smart Watch X" },
  { id: "P003", name: "Coffee Beans 1kg" },
  { id: "P004", name: "Winter Coat" },
  { id: "P005", name: "Yoga Mat" },
];

export default function Scenarios() {
  const [product, setProduct] = useState("ALL");
  const [priceChangePct, setPriceChangePct] = useState(0);
  const [horizon, setHorizon] = useState(30);

  const simulateMutation = useMutation({
    mutationFn: () =>
      postSimulate({
        product,
        price_change_pct: priceChangePct,
        horizon,
      }),
  });

  return (
    <div className="flex flex-col gap-8 pb-8 animate-fade-in max-w-[1200px] mx-auto">
      <div>
        <h1 className="text-3xl font-display font-bold tracking-tight">What-If Scenarios</h1>
        <p className="text-muted-foreground mt-2 max-w-3xl leading-relaxed">
          Simulate changes to business levers like pricing and see the AI-predicted impact on
          future sales volume.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="glass p-6 rounded-2xl flex flex-col gap-6 col-span-1 lg:col-span-1 border border-white/20 dark:border-white/5">
          <div className="flex items-center gap-2 border-b border-border/50 pb-4">
            <Settings2 className="w-5 h-5 text-primary" />
            <h2 className="font-semibold text-lg">Parameters</h2>
          </div>

          <div className="flex flex-col gap-2">
            <label className="text-sm font-medium">Target Product</label>
            <select
              value={product}
              onChange={(e) => setProduct(e.target.value)}
              className="p-2.5 rounded-xl border border-input bg-background text-foreground text-sm focus:ring-2 focus:ring-primary/20 outline-none transition-all"
            >
              {PRODUCTS.map((p) => (
                <option key={p.id} value={p.id} className="bg-background text-foreground">
                  {p.name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex flex-col gap-2">
            <div className="flex justify-between items-center">
              <label className="text-sm font-medium">Price Adjustment</label>
              <span className="text-xs font-bold text-primary">{priceChangePct > 0 ? "+" : ""}{priceChangePct}%</span>
            </div>
            <input
              type="range"
              min="-30"
              max="30"
              step="1"
              value={priceChangePct}
              onChange={(e) => setPriceChangePct(Number(e.target.value))}
              className="w-full accent-primary"
            />
            <div className="flex justify-between text-[10px] text-muted-foreground">
              <span>-30% Discount</span>
              <span>+30% Premium</span>
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <label className="text-sm font-medium">Simulation Horizon</label>
            <div className="flex items-center gap-4">
              <input
                type="number"
                min="7"
                max="90"
                value={horizon}
                onChange={(e) => setHorizon(Number(e.target.value))}
                className="w-20 p-2 rounded-xl border border-input bg-background/50 text-sm"
              />
              <span className="text-sm text-muted-foreground">Days</span>
            </div>
          </div>

          <button
            onClick={() => simulateMutation.mutate()}
            disabled={simulateMutation.isPending}
            className="mt-auto flex items-center justify-center gap-2 w-full py-3 rounded-xl bg-primary text-primary-foreground font-medium hover:opacity-90 transition-opacity disabled:opacity-50"
          >
            {simulateMutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Brain className="w-4 h-4" />
            )}
            Run Simulation
          </button>
        </div>

        <div className="glass p-6 rounded-2xl flex flex-col gap-6 col-span-1 lg:col-span-3 border border-white/20 dark:border-white/5 min-h-[500px]">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-lg flex items-center gap-2">
              <ArrowRight className="w-5 h-5 text-primary" />
              Simulation Results
            </h2>
          </div>

          {!simulateMutation.data && !simulateMutation.isPending && (
            <div className="flex-1 flex flex-col items-center justify-center text-center text-muted-foreground border-2 border-dashed border-border/50 rounded-xl bg-secondary/20">
              <Brain className="w-12 h-12 mb-4 opacity-20" />
              <p>Configure parameters on the left and run the simulation.</p>
            </div>
          )}

          {simulateMutation.isPending && (
            <div className="flex-1 flex flex-col items-center justify-center">
              <Loader2 className="w-8 h-8 animate-spin text-primary mb-4" />
              <p className="text-sm text-muted-foreground">Running XGBoost Surrogate Model...</p>
            </div>
          )}

          {simulateMutation.data && (
            <div className="flex-1 w-full h-[400px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={simulateMutation.data.points} margin={{ top: 20, right: 10, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorBaseline" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#94a3b8" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#94a3b8" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="colorScenario" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.1)" />
                  <XAxis 
                    dataKey="date" 
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
                    tickFormatter={(val) => val.slice(5)}
                    minTickGap={30}
                  />
                  <YAxis 
                    axisLine={false}
                    tickLine={false}
                    tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
                    tickFormatter={(val) => `$${(val / 1000).toFixed(0)}k`}
                  />
                  <Tooltip 
                    contentStyle={{ backgroundColor: 'hsl(var(--card))', color: 'hsl(var(--card-foreground))', borderRadius: '12px', border: '1px solid hsl(var(--border))', boxShadow: '0 10px 30px -10px rgba(0,0,0,0.1)' }}
                    itemStyle={{ color: 'hsl(var(--card-foreground))' }}
                    formatter={(val: number) => [`$${val.toLocaleString()}`, ""]}
                  />
                  <Area
                    type="monotone"
                    dataKey="baseline"
                    name="Baseline (No Change)"
                    stroke="#94a3b8"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorBaseline)"
                  />
                  <Area
                    type="monotone"
                    dataKey="scenario"
                    name={`Scenario (${simulateMutation.data.price_change_pct > 0 ? "+" : ""}${simulateMutation.data.price_change_pct}% Price)`}
                    stroke="#6366f1"
                    strokeWidth={3}
                    fillOpacity={1}
                    fill="url(#colorScenario)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
