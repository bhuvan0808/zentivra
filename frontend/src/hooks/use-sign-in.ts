import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { login } from "@/lib/api";

export interface UseSignInReturn {
  username: string;
  setUsername: (v: string) => void;
  password: string;
  setPassword: (v: string) => void;
  loading: boolean;
  fieldErrors: Record<string, string>;
  handleSubmit: (e: React.FormEvent) => Promise<void>;
  redirectTo: string;
}

/**
 * Custom hook for the Sign In page.
 * Manages form state, validation, authentication API calls, and redirection.
 *
 * Interacts with:
 * - POST /api/auth/login
 */
export function useSignIn(): UseSignInReturn {
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

  return {
    username,
    setUsername,
    password,
    setPassword,
    loading,
    fieldErrors,
    handleSubmit,
    redirectTo,
  };
}