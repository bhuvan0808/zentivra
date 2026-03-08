"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { getMe } from "@/lib/api";
import { toast } from "sonner";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname(); // keep for fallback/render purposes if needed elsewhere, though only used initially now
  const [status, setStatus] = useState<"checking" | "authenticated">(
    "checking",
  );

  useEffect(() => {
    const token = localStorage.getItem("auth_token");
    const currentPath = window.location.pathname;

    if (!token) {
      router.replace(`/?redirect=${encodeURIComponent(currentPath)}`);
      return;
    }

    let cancelled = false;

    getMe().then((res) => {
      if (cancelled) return;

      if (res.ok) {
        setStatus("authenticated");
      } else {
        localStorage.removeItem("auth_token");
        toast.warning("Session expired. Please login again.");
        router.replace(`/?redirect=${encodeURIComponent(currentPath)}`);
      }
    });

    return () => {
      cancelled = true;
    };
  }, [router]);

  if (status === "checking") {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <Loader2 className="size-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return <>{children}</>;
}
