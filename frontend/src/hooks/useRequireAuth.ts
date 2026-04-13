import { useEffect } from "react";
import { useRouter } from "next/router";
import { useAuth } from "@/context/AuthContext";

const PUBLIC_PATHS = ["/login", "/register"];

/**
 * Redirect unauthenticated users to login.
 * Returns { user, loading, isAdmin } — render null while loading.
 */
export function useRequireAuth() {
  const { user, loading, isAdmin } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user && !PUBLIC_PATHS.includes(router.pathname)) {
      router.replace("/login");
    }
  }, [user, loading, router]);

  return { user, loading, isAdmin, ready: !loading && !!user };
}
