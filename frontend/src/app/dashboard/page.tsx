"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { apiFetch, roleHome, clearAuth } from "@/lib/api";

export default function DashboardRedirect() {
  const router = useRouter();
  useEffect(() => {
    (async () => {
      const token = localStorage.getItem("token");
      if (!token) { router.replace("/login"); return; }
      const res = await apiFetch("/auth/me");
      if (!res.ok) { clearAuth(); router.replace("/login"); return; }
      const me = await res.json();
      router.replace(roleHome(me.role));
    })();
  }, [router]);
  return <div className="page-shell"><div className="loading-panel">Opening your dashboard…</div></div>;
}
