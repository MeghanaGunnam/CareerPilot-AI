"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  Suspense,
  useEffect,
  useRef,
  useState,
} from "react";

import { verifyEmail } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";

type VerificationStatus =
  | "verifying"
  | "success"
  | "error";

function VerificationLoading() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-6">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <Link
          href="/"
          className="text-xl font-bold text-slate-950"
        >
          CareerPilot AI
        </Link>

        <div className="mt-8">
          <div className="mb-5 h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-blue-600" />

          <h1 className="text-2xl font-semibold text-slate-950">
            Loading verification
          </h1>

          <p className="mt-3 leading-7 text-slate-600">
            Preparing your email verification...
          </p>
        </div>
      </div>
    </main>
  );
}

function VerifyEmailContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const hasStarted = useRef(false);

  const [status, setStatus] =
    useState<VerificationStatus>("verifying");

  const [message, setMessage] = useState(
    "Verifying your email address..."
  );

  useEffect(() => {
    if (!token || hasStarted.current) {
      return;
    }

    hasStarted.current = true;

    const verificationToken = token;

    async function verify() {
      try {
        await verifyEmail(verificationToken);

        setStatus("success");

        setMessage(
          "Your email address has been verified successfully."
        );
      } catch (error) {
        setStatus("error");

        if (error instanceof ApiError) {
          setMessage(error.message);
        } else {
          setMessage(
            "Unable to verify your email. Please try again."
          );
        }
      }
    }

    void verify();
  }, [token]);

  const effectiveStatus: VerificationStatus =
    token ? status : "error";

  const effectiveMessage = token
    ? message
    : "The verification link is invalid or incomplete.";

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-6">
      <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <Link
          href="/"
          className="text-xl font-bold text-slate-950"
        >
          CareerPilot AI
        </Link>

        <div className="mt-8">
          {effectiveStatus === "verifying" && (
            <>
              <div className="mb-5 h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-blue-600" />

              <h1 className="text-2xl font-semibold text-slate-950">
                Verifying email
              </h1>
            </>
          )}

          {effectiveStatus === "success" && (
            <>
              <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-full bg-green-100 text-xl font-bold text-green-700">
                ✓
              </div>

              <h1 className="text-2xl font-semibold text-slate-950">
                Email verified
              </h1>
            </>
          )}

          {effectiveStatus === "error" && (
            <>
              <div className="mb-5 flex h-12 w-12 items-center justify-center rounded-full bg-red-100 text-xl font-bold text-red-700">
                !
              </div>

              <h1 className="text-2xl font-semibold text-slate-950">
                Verification failed
              </h1>
            </>
          )}

          <p className="mt-3 leading-7 text-slate-600">
            {effectiveMessage}
          </p>

          {effectiveStatus === "success" && (
            <Link
              href="/login"
              className="mt-8 block w-full rounded-xl bg-slate-950 px-4 py-3 text-center font-medium text-white transition hover:bg-slate-800"
            >
              Continue to sign in
            </Link>
          )}

          {effectiveStatus === "error" && (
            <Link
              href="/login"
              className="mt-8 block w-full rounded-xl border border-slate-300 px-4 py-3 text-center font-medium text-slate-700 transition hover:bg-slate-50"
            >
              Return to sign in
            </Link>
          )}
        </div>
      </div>
    </main>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<VerificationLoading />}>
      <VerifyEmailContent />
    </Suspense>
  );
}