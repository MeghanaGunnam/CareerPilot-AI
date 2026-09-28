"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import {
  getCurrentUser,
  logout,
  type User,
} from "@/lib/api/auth";

export default function DashboardPage() {
  const router = useRouter();

  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadUser() {
      const accessToken = sessionStorage.getItem(
        "careerpilot_access_token"
      );

      if (!accessToken) {
        router.replace("/login");
        return;
      }

      try {
        const currentUser = await getCurrentUser(
          accessToken
        );

        setUser(currentUser);
      } catch {
        sessionStorage.removeItem(
          "careerpilot_access_token"
        );

        sessionStorage.removeItem(
          "careerpilot_refresh_token"
        );

        router.replace("/login");
      } finally {
        setIsLoading(false);
      }
    }

    loadUser();
  }, [router]);

  async function handleLogout() {
    const accessToken = sessionStorage.getItem(
      "careerpilot_access_token"
    );

    const refreshToken = sessionStorage.getItem(
      "careerpilot_refresh_token"
    );

    try {
      if (accessToken && refreshToken) {
        await logout(
          accessToken,
          refreshToken
        );
      }
    } catch (error) {
      console.error("Logout request failed:", error);
    } finally {
      sessionStorage.removeItem(
        "careerpilot_access_token"
      );

      sessionStorage.removeItem(
        "careerpilot_refresh_token"
      );

      router.replace("/login");
    }
  }

  if (isLoading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-50">
        <p className="text-slate-600">
          Loading CareerPilot...
        </p>
      </main>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <main className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
          <h1 className="text-xl font-bold text-slate-950">
            CareerPilot AI
          </h1>

          <div className="flex items-center gap-4">
            <span className="text-sm text-slate-600">
              {user.email}
            </span>

            <button
              type="button"
              onClick={handleLogout}
              className="rounded-lg bg-slate-950 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800"
            >
              Sign out
            </button>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-7xl px-6 py-12">
        <p className="text-sm font-semibold uppercase tracking-wider text-blue-600">
          Dashboard
        </p>

        <h2 className="mt-2 text-4xl font-semibold tracking-tight text-slate-950">
          Welcome to CareerPilot AI
        </h2>

        <p className="mt-4 max-w-2xl text-slate-600">
          Your authenticated CareerPilot workspace is
          ready. We&apos;ll build your career profile,
          evidence graph, recommendations, readiness
          insights, and adaptive career plan here.
        </p>

        <div className="mt-10 rounded-2xl border border-slate-200 bg-white p-6">
          <p className="text-sm text-slate-500">
            Signed in as
          </p>

          <p className="mt-1 font-medium text-slate-950">
            {user.email}
          </p>

          <p className="mt-4 text-sm text-slate-500">
            Account verification
          </p>

          <p className="mt-1 font-medium text-slate-950">
            {user.is_verified
              ? "Verified"
              : "Not verified"}
          </p>
        </div>
      </section>
    </main>
  );
}