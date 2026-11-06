"use client";

import { useState } from "react";
import { useAuth } from "@/hooks/useAuth";

export default function SignoutButton({ className = "" }) {
  const { status, signout } = useAuth();
  const [signingOut, setSigningOut] = useState(false);

  if (status !== "authenticated") return null;

  const handleSignout = async () => {
    setSigningOut(true);
    try {
      await signout();
    } finally {
      // A full navigation drops every in-memory store along with the session.
      window.location.assign("/signin");
    }
  };

  return (
    <button
      onClick={handleSignout}
      disabled={signingOut}
      className={`rounded-full px-3 py-1.5 text-[15px] font-medium text-muted transition-colors hover:text-ink disabled:opacity-50 ${className}`}
    >
      {signingOut ? "Signing out…" : "Sign out"}
    </button>
  );
}
