"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { login } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";

export default function LoginPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setError("");
    setIsLoading(true);

    try {
      const tokens = await login({
        email,
        password,
      });

      sessionStorage.setItem(
        "careerpilot_access_token",
        tokens.access_token
      );

      sessionStorage.setItem(
        "careerpilot_refresh_token",
        tokens.refresh_token
      );

      router.push("/dashboard");
    } catch (error) {
      if (error instanceof ApiError) {
        setError(error.message);
      } else {
        setError(
          "Unable to sign in. Please try again."
        );
      }
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="flex min-h-screen bg-slate-50">
      <section className="hidden w-1/2 flex-col justify-between bg-slate-950 p-14 text-white lg:flex">
        <div>
          <Link
            href="/"
            className="text-2xl font-bold tracking-tight"
          >
            CareerPilot AI
          </Link>

          <div className="mt-28 max-w-xl">
            <p className="mb-4 text-sm font-semibold uppercase tracking-[0.2em] text-blue-400">
              Adaptive Career Intelligence
            </p>

            <h1 className="text-5xl font-semibold leading-tight">
              Build your career with evidence,
              not guesswork.
            </h1>

            <p className="mt-6 max-w-lg text-lg leading-8 text-slate-300">
              Understand your skills, discover suitable
              career paths, identify gaps, and build an
              adaptive plan toward your goals.
            </p>
          </div>
        </div>

        <p className="text-sm text-slate-500">
          CareerPilot AI
        </p>
      </section>

      <section className="flex w-full items-center justify-center px-6 py-12 lg:w-1/2">
        <div className="w-full max-w-md">
          <div className="mb-10 lg:hidden">
            <Link
              href="/"
              className="text-2xl font-bold text-slate-950"
            >
              CareerPilot AI
            </Link>
          </div>

          <div>
            <h2 className="text-3xl font-semibold tracking-tight text-slate-950">
              Welcome back
            </h2>

            <p className="mt-2 text-slate-600">
              Sign in to continue your career journey.
            </p>
          </div>

          <form
            onSubmit={handleSubmit}
            className="mt-8 space-y-5"
          >
            <div>
              <label
                htmlFor="email"
                className="mb-2 block text-sm font-medium text-slate-700"
              >
                Email address
              </label>

              <input
                id="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(event) =>
                  setEmail(event.target.value)
                }
                placeholder="you@example.com"
                className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-slate-950 outline-none transition focus:border-blue-600 focus:ring-4 focus:ring-blue-100"
              />
            </div>

            <div>
              <div className="mb-2 flex items-center justify-between">
                <label
                  htmlFor="password"
                  className="text-sm font-medium text-slate-700"
                >
                  Password
                </label>

                <span className="text-sm text-slate-400">
                  Forgot password?
                </span>
              </div>

              <input
                id="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(event) =>
                  setPassword(event.target.value)
                }
                placeholder="Enter your password"
                className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-slate-950 outline-none transition focus:border-blue-600 focus:ring-4 focus:ring-blue-100"
              />
            </div>

            {error && (
              <div
                role="alert"
                className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
              >
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full rounded-xl bg-slate-950 px-4 py-3 font-medium text-white transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isLoading
                ? "Signing in..."
                : "Sign in"}
            </button>
          </form>

          <p className="mt-8 text-center text-sm text-slate-600">
            New to CareerPilot?{" "}
            <Link
              href="/register"
              className="font-semibold text-blue-600 hover:text-blue-700"
            >
              Create an account
            </Link>
          </p>
        </div>
      </section>
    </main>
  );
}