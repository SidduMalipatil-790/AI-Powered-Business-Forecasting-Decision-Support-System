import { AlertCircle, RotateCw } from "lucide-react";
import { Button } from "@/components/ui/button";

export function ErrorState({ message, onRetry }: { message?: string; onRetry?: () => void }) {
  return (
    <div className="glass rounded-2xl p-8 text-center">
      <div className="mx-auto h-12 w-12 rounded-full bg-danger/10 text-danger flex items-center justify-center mb-3">
        <AlertCircle className="h-6 w-6" />
      </div>
      <div className="font-semibold mb-1">Something went wrong</div>
      <p className="text-sm text-muted-foreground mb-4">{message || "Failed to load data. Please try again."}</p>
      {onRetry && (
        <Button onClick={onRetry} variant="outline" size="sm" className="rounded-full">
          <RotateCw className="h-3 w-3 mr-2" /> Retry
        </Button>
      )}
    </div>
  );
}
