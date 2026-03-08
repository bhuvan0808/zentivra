"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

export function ThemeToggle() {
  const { setTheme, resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    // Avoid setting state synchronously during render by pushing it to the end of the event loop
    const timeoutId = setTimeout(() => {
      setMounted(true);
    }, 0);
    return () => clearTimeout(timeoutId);
  }, []);

  if (!mounted) return null;

  const isDark = resolvedTheme === "dark";

  return (
    <div className="fixed bottom-5 right-5 z-50">
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            onClick={() => setTheme(isDark ? "light" : "dark")}
            className="group relative flex size-11 items-center justify-center rounded-full border border-white/20 bg-white/10 shadow-[0_8px_32px_rgba(0,0,0,0.12)] backdrop-blur-xl backdrop-saturate-150 transition-all duration-300 hover:scale-105 hover:border-white/30 hover:bg-white/15 hover:shadow-[0_8px_32px_rgba(0,0,0,0.2)] active:scale-95 dark:border-white/10 dark:bg-white/5 dark:shadow-[0_8px_32px_rgba(0,0,0,0.4)] dark:hover:border-white/20 dark:hover:bg-white/10"
          >
            <div className="absolute inset-0 rounded-full bg-gradient-to-br from-white/20 to-transparent opacity-60" />
            {isDark ? (
              <Sun className="relative size-4 text-amber-300 drop-shadow-[0_0_6px_rgba(251,191,36,0.4)] transition-transform duration-300 group-hover:rotate-45" />
            ) : (
              <Moon className="relative size-4 text-slate-700 drop-shadow-[0_0_4px_rgba(0,0,0,0.1)] transition-transform duration-300 group-hover:-rotate-12" />
            )}
            <span className="sr-only">Toggle theme</span>
          </button>
        </TooltipTrigger>
        <TooltipContent side="left">
          Switch to {isDark ? "light" : "dark"} mode
        </TooltipContent>
      </Tooltip>
    </div>
  );
}
