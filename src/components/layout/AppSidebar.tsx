import { Link, useLocation } from "react-router-dom";
import { LayoutDashboard, TrendingUp, Lightbulb, AlertTriangle, Brain, Settings2 } from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";

const items = [
  { title: "Dashboard", url: "/", icon: LayoutDashboard },
  { title: "Forecasting", url: "/forecasting", icon: TrendingUp },
  { title: "Scenarios", url: "/scenarios", icon: Settings2 },
  { title: "Decisions", url: "/decisions", icon: Lightbulb },
  { title: "Anomalies", url: "/anomalies", icon: AlertTriangle },
];

export function AppSidebar() {
  const { state } = useSidebar();
  const collapsed = state === "collapsed";
  const { pathname } = useLocation();
  const isActive = (path: string) => (path === "/" ? pathname === "/" : pathname.startsWith(path));

  return (
    <Sidebar collapsible="icon" className="border-r border-border/50">
      <SidebarContent className="bg-sidebar">
        <div className="p-4 flex items-center gap-2.5">
          <div className="h-9 w-9 rounded-xl bg-gradient-primary flex items-center justify-center shadow-elevated shrink-0">
            <Brain className="h-5 w-5 text-primary-foreground" />
          </div>
          {!collapsed && (
            <div className="overflow-hidden">
              <div className="font-display font-bold text-base leading-tight">Forecast IQ</div>
              <div className="text-[10px] uppercase tracking-wider text-muted-foreground">AI Decision Suite</div>
            </div>
          )}
        </div>

        <SidebarGroup>
          <SidebarGroupLabel>Workspace</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {items.map((item) => {
                const active = isActive(item.url);
                return (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton 
                      asChild 
                      isActive={active}
                      className={active ? "bg-gradient-primary text-primary-foreground shadow-elevated hover:bg-gradient-primary hover:text-primary-foreground" : "text-sidebar-foreground"}
                    >
                      <Link to={item.url} className="flex items-center gap-3">
                        <item.icon className="h-4 w-4 shrink-0" />
                        {!collapsed && <span className="font-medium">{item.title}</span>}
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {!collapsed && (
          <div className="mt-auto p-4">
            <div className="glass rounded-xl p-4">
              <div className="text-xs font-semibold mb-1">Pro tip</div>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Connect a backend by setting <code className="text-primary">VITE_API_BASE_URL</code>.
              </p>
            </div>
          </div>
        )}
      </SidebarContent>
    </Sidebar>
  );
}
