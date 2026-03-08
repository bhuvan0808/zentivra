"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Loader2 } from "lucide-react";
import { getMe } from "@/lib/api";

function PublicGuardContent({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<"checking" | "guest" | "redirecting">("checking");
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const token = localStorage.getItem("auth_token");

    if (!token) {
      setTimeout(() => setStatus("guest"), 0);
      return;
    }

    let cancelled = false;

    getMe().then((res) => {
      if (cancelled) return;

      if (res.ok) {
        setStatus("redirecting");
        const redirect = searchParams.get("redirect") || "/dashboard";
        router.replace(redirect);
      } else {
        // Token exists but is invalid/expired
        localStorage.removeItem("auth_token");
        setStatus("guest");
      }
    }).catch(() => {
      if (cancelled) return;
      // On network error, treat as guest so they can at least see the public page
      setStatus("guest");
    });

    return () => {
      cancelled = true;
    };
  }, [router, searchParams]);

  if (status === "checking" || status === "redirecting") {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <Loader2 className="size-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return <>{children}</>;
}

export function PublicGuard({ children }: { children: React.ReactNode }) {
  return (
    <Suspense
      fallback={
        <div className="flex h-screen w-full items-center justify-center">
          <Loader2 className="size-6 animate-spin text-muted-foreground" />
        </div>
      }
    >
      <PublicGuardContent>{children}</PublicGuardContent>
    </Suspense>
  );
}
