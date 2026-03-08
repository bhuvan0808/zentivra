"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Radar, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
import { LiquidBlob } from "@/components/liquid-blob";
import { login } from "@/lib/api";

import { PublicGuard } from "@/components/public-guard";

function SignInForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectTo = searchParams.get("redirect") || "/dashboard";

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  function validate(): boolean {
    const errors: Record<string, string> = {};
    if (!username.trim()) errors.username = "Username or Email is required";
    else if (username.length > 100) errors.username = "Max 100 characters";
    if (!password) errors.password = "Password is required";
    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    const res = await login({ username: username.trim(), password });
    setLoading(false);

    if (res.ok) {
      localStorage.setItem("auth_token", res.data.auth_token);
      localStorage.setItem("user_email", res.data.email);
      toast.success(`Welcome back, ${res.data.display_name}!`);
      router.push(redirectTo);
    } else {
      toast.error(res.error);
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="relative z-10 w-full max-w-sm"
    >
      <div className="mb-8 flex flex-col items-center gap-2">
        <Link
          href="/"
          className="mb-1 inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="size-3" />
          Back to home
        </Link>
        <Link href="/" className="flex items-center gap-2">
          <Radar className="size-7 text-primary" />
          <span className="text-xl font-bold tracking-tight font-display">
            Zentivra
          </span>
        </Link>
        <p className="text-sm text-muted-foreground">Sign in to your account</p>
      </div>

      <Card
        style={{ filter: "blur(0px)" }}
        className="border-white/10 bg-card/30 backdrop-blur-xl backdrop-saturate-150 shadow-sm"
      >
        <CardContent className="pt-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2.5">
              <Label htmlFor="username">Username or Email</Label>
              <Input
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="john_doe or john@example.com"
                autoComplete="username"
                autoFocus
              />
              {fieldErrors.username && (
                <p className="field-error">{fieldErrors.username}</p>
              )}
            </div>

            <div className="space-y-2.5">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                autoComplete="current-password"
              />
              {fieldErrors.password && (
                <p className="field-error">{fieldErrors.password}</p>
              )}
            </div>

            <Button type="submit" className="w-full" disabled={loading}>
              {loading && <Loader2 className="mr-1.5 size-4 animate-spin" />}
              {loading ? "Signing in..." : "Sign In"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <p className="mt-6 text-center text-sm text-muted-foreground">
        Don&apos;t have an account?{" "}
        <Link
          href={
            redirectTo !== "/dashboard"
              ? `/signup?redirect=${encodeURIComponent(redirectTo)}`
              : "/signup"
          }
          className="font-medium text-primary hover:underline"
        >
          Sign up
        </Link>
      </p>
    </motion.div>
  );
}

export default function SignInPage() {
  return (
    <div className="relative flex min-h-screen items-center justify-center bg-background px-4">
      <LiquidBlob />
      <div
        aria-hidden
        className="pointer-events-none fixed inset-0 z-1 overflow-hidden"
      >
        <div className="absolute -top-24 left-1/4 h-120 w-120 rounded-full bg-indigo-500/20 blur-[120px]" />
        <div className="absolute top-1/3 right-[10%] h-100 w-100 rounded-full bg-violet-500/15 blur-[100px]" />
        <div className="absolute bottom-[15%] left-[15%] h-88 w-88 rounded-full bg-purple-500/15 blur-[110px]" />
      </div>
      <PublicGuard>
        <SignInForm />
      </PublicGuard>
    </div>
  );
}
