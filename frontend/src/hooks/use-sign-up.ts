import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { signup } from "@/lib/api";

export interface UseSignUpReturn {
  displayName: string;
  setDisplayName: (v: string) => void;
  username: string;
  setUsername: (v: string) => void;
  email: string;
  setEmail: (v: string) => void;
  password: string;
  setPassword: (v: string) => void;
  confirmPassword: string;
  setConfirmPassword: (v: string) => void;
  loading: boolean;
  fieldErrors: Record<string, string>;
  handleSubmit: (e: React.FormEvent) => Promise<void>;
  redirectTo: string;
}

/**
 * Custom hook for the Sign Up page.
 * Manages form state, validation, registration API calls, and redirection.
 *
 * Interacts with:
 * - POST /api/auth/signup
 */
export function useSignUp(): UseSignUpReturn {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectTo = searchParams.get("redirect") || "/dashboard";

  const [displayName, setDisplayName] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  function validate(): boolean {
    const errors: Record<string, string> = {};
    if (!displayName.trim()) errors.displayName = "Display name is required";
    else if (displayName.length > 150)
      errors.displayName = "Max 150 characters";

    if (!username.trim()) errors.username = "Username is required";
    else if (username.length < 3) errors.username = "At least 3 characters";
    else if (username.length > 100) errors.username = "Max 100 characters";

    const emailRegex = /^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$/;
    if (!email.trim()) errors.email = "Email is required";
    else if (!emailRegex.test(email)) errors.email = "Invalid email format";

    if (!password) errors.password = "Password is required";
    else if (password.length < 8) errors.password = "At least 8 characters";

    if (!confirmPassword)
      errors.confirmPassword = "Please confirm your password";
    else if (password !== confirmPassword)
      errors.confirmPassword = "Passwords do not match";

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    const res = await signup({
      username: username.trim(),
      email: email.trim(),
      password,
      display_name: displayName.trim(),
    });
    setLoading(false);

    if (res.ok) {
      localStorage.setItem("auth_token", res.data.auth_token);
      localStorage.setItem("user_email", res.data.email);
      toast.success(`Welcome to the community, ${res.data.display_name}!`);
      router.push(redirectTo);
    } else {
      toast.error(res.error);
    }
  }

  return {
    displayName,
    setDisplayName,
    username,
    setUsername,
    email,
    setEmail,
    password,
    setPassword,
    confirmPassword,
    setConfirmPassword,
    loading,
    fieldErrors,
    handleSubmit,
    redirectTo,
  };
}