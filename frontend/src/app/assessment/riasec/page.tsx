"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import {
  getRiasecQuestions,
  submitRiasecAssessment,
  type RiasecQuestionnaire,
} from "@/lib/api/psychometrics";

const ACCESS_TOKEN_KEY = "careerpilot_access_token";

export default function RiasecAssessmentPage() {
  const router = useRouter();

  const [questionnaire, setQuestionnaire] =
    useState<RiasecQuestionnaire | null>(null);

  const [currentIndex, setCurrentIndex] = useState(0);

  const [answers, setAnswers] = useState<
    Record<string, number>
  >({});

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  const [error, setError] = useState<string | null>(
    null
  );

  useEffect(() => {
    async function loadQuestionnaire() {
      const accessToken = sessionStorage.getItem(
        ACCESS_TOKEN_KEY
      );

      if (!accessToken) {
        router.replace("/login");
        return;
      }

      try {
        const data = await getRiasecQuestions(
          accessToken
        );

        setQuestionnaire(data);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Unable to load the assessment."
        );
      } finally {
        setLoading(false);
      }
    }

    void loadQuestionnaire();
  }, [router]);

  const answeredCount = useMemo(
    () => Object.keys(answers).length,
    [answers]
  );

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-50 px-6">
        <div className="text-center">
          <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-blue-600" />

          <p className="mt-4 text-sm text-slate-600">
            Loading your career interest assessment...
          </p>
        </div>
      </main>
    );
  }

  if (error || !questionnaire) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-50 px-6">
        <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 text-center shadow-sm">
          <h1 className="text-xl font-semibold text-slate-900">
            Unable to load assessment
          </h1>

          <p className="mt-3 text-sm leading-6 text-slate-600">
            {error ??
              "The assessment could not be loaded."}
          </p>

          <button
            type="button"
            onClick={() => window.location.reload()}
            className="mt-6 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-blue-700"
          >
            Try Again
          </button>
        </div>
      </main>
    );
  }

  const currentQuestion =
    questionnaire.questions[currentIndex];

  const totalQuestions =
    questionnaire.questions.length;

  const progress =
    ((currentIndex + 1) / totalQuestions) * 100;

  const selectedValue =
    answers[currentQuestion.id];

  function selectAnswer(value: number) {
    setAnswers((previous) => ({
      ...previous,
      [currentQuestion.id]: value,
    }));

    setError(null);
  }

  function goPrevious() {
    if (currentIndex > 0) {
      setCurrentIndex((previous) => previous - 1);
      setError(null);
    }
  }

  function goNext() {
    if (selectedValue === undefined) {
      setError(
        "Please select an answer before continuing."
      );
      return;
    }

    if (currentIndex < totalQuestions - 1) {
      setCurrentIndex((previous) => previous + 1);
      setError(null);
    }
  }

  async function submitAssessment() {
    if (selectedValue === undefined) {
      setError(
        "Please select an answer before submitting."
      );
      return;
    }

    if (answeredCount !== totalQuestions) {
      setError(
        `Please answer all ${totalQuestions} questions before submitting.`
      );
      return;
    }

    const accessToken = sessionStorage.getItem(
      ACCESS_TOKEN_KEY
    );

    if (!accessToken) {
      router.replace("/login");
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const formattedAnswers =
        questionnaire.questions.map((question) => ({
          question_id: question.id,
          response_value: answers[question.id],
        }));

      await submitRiasecAssessment(
        accessToken,
        formattedAnswers
      );

      router.push("/assessment/riasec/results");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Unable to submit your assessment."
      );
    } finally {
      setSubmitting(false);
    }
  }

  const isLastQuestion =
    currentIndex === totalQuestions - 1;

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-4xl px-5 py-10 sm:px-8 lg:py-16">
        <header className="mb-8">
          <button
            type="button"
            onClick={() => router.push("/dashboard")}
            className="mb-6 text-sm font-medium text-slate-500 transition hover:text-slate-900"
          >
            ← Back to dashboard
          </button>

          <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-sm font-semibold uppercase tracking-wider text-blue-600">
                CareerPilot AI
              </p>

              <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">
                Career Interest Assessment
              </h1>

              <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600">
                {questionnaire.instructions}
              </p>
            </div>

            <div className="shrink-0 text-sm font-medium text-slate-600">
              {answeredCount}/{totalQuestions} answered
            </div>
          </div>
        </header>

        <section className="mb-6">
          <div className="mb-2 flex items-center justify-between text-sm">
            <span className="font-medium text-slate-700">
              Question {currentIndex + 1} of{" "}
              {totalQuestions}
            </span>

            <span className="text-slate-500">
              {Math.round(progress)}%
            </span>
          </div>

          <div className="h-2 overflow-hidden rounded-full bg-slate-200">
            <div
              className="h-full rounded-full bg-blue-600 transition-all duration-300"
              style={{
                width: `${progress}%`,
              }}
            />
          </div>
        </section>

        <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-10">
          <div className="mb-8">
            <span className="inline-flex rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
              Question {currentIndex + 1}
            </span>

            <h2 className="mt-5 text-2xl font-semibold leading-9 text-slate-950">
              {currentQuestion.text}
            </h2>

            <p className="mt-2 text-sm text-slate-500">
              Choose the option that best reflects your
              genuine preference.
            </p>
          </div>

          <div className="space-y-3">
            {questionnaire.response_options.map(
              (option) => {
                const selected =
                  selectedValue === option.value;

                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() =>
                      selectAnswer(option.value)
                    }
                    className={`flex w-full items-center gap-4 rounded-xl border p-4 text-left transition ${
                      selected
                        ? "border-blue-600 bg-blue-50 ring-1 ring-blue-600"
                        : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50"
                    }`}
                  >
                    <span
                      className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full border ${
                        selected
                          ? "border-blue-600"
                          : "border-slate-300"
                      }`}
                    >
                      {selected && (
                        <span className="h-2.5 w-2.5 rounded-full bg-blue-600" />
                      )}
                    </span>

                    <span
                      className={`text-sm font-medium ${
                        selected
                          ? "text-blue-900"
                          : "text-slate-700"
                      }`}
                    >
                      {option.label}
                    </span>
                  </button>
                );
              }
            )}
          </div>

          {error && (
            <div className="mt-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <div className="mt-10 flex items-center justify-between gap-4 border-t border-slate-100 pt-6">
            <button
              type="button"
              onClick={goPrevious}
              disabled={
                currentIndex === 0 || submitting
              }
              className="rounded-lg border border-slate-300 px-5 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
            >
              Previous
            </button>

            {!isLastQuestion ? (
              <button
                type="button"
                onClick={goNext}
                disabled={submitting}
                className="rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                Next
              </button>
            ) : (
              <button
                type="button"
                onClick={submitAssessment}
                disabled={submitting}
                className="rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {submitting
                  ? "Analyzing..."
                  : "View My Results"}
              </button>
            )}
          </div>
        </section>

        <p className="mx-auto mt-6 max-w-2xl text-center text-xs leading-5 text-slate-500">
          Your responses are used to understand your
          career-interest profile and identify
          interest-aligned occupations. They do not
          predict employment or career success.
        </p>
      </div>
    </main>
  );
}