"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { ApiError } from "@/lib/api/client";

import {
  AssessmentDetail,
  AssessmentAttemptSummary,
  AssessmentRecommendation,
  AssessmentSubmissionResponse,
  AssessmentSummary,
  CareerAssessmentRecommendationsResponse,
  getAssessment,
  getAssessmentAttempt,
  getAssessmentAttempts,
  getAssessments,
  getMyAssessmentRecommendations,
  submitAssessment,
} from "@/lib/api/assessments";
const ACCESS_TOKEN_KEY = "careerpilot_access_token";



type Answers = Record<string, string>;

function errorMessage(error: unknown, fallback: string) {
  if (error instanceof ApiError && error.status === 401) {
    return "Your session has expired. Please sign in again to continue.";
  }
  if (error instanceof ApiError && error.status === 403) {
    return "You do not have permission to access this assessment or attempt.";
  }
  return error instanceof Error ? error.message : fallback;
}

function formatDate(value: string | null) {
  return value ? new Date(value).toLocaleString() : "Not completed";
}

function formatDifficulty(value: string) {
  return value
    .toLowerCase()
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

export default function AssessmentPage() {
  const router = useRouter();

  const [assessments, setAssessments] = useState<AssessmentSummary[]>([]);
  const [recommendations, setRecommendations] =
  useState<CareerAssessmentRecommendationsResponse | null>(null);

  

  const [resolvedCareerId, setResolvedCareerId] =
  useState<string | null>(null);

  const [activeAssessment, setActiveAssessment] =
    useState<AssessmentDetail | null>(null);

  const [answers, setAnswers] = useState<Answers>({});

  const [result, setResult] =
    useState<AssessmentSubmissionResponse | null>(null);

  const [loading, setLoading] = useState(true);
  const [openingId, setOpeningId] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const submitGuard = useRef(false);
  const openingGuard = useRef(false);
  const [confirming, setConfirming] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [attempts, setAttempts] = useState<AssessmentAttemptSummary[] | null>(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState("");
  const [historyOffset, setHistoryOffset] = useState(0);

  const [error, setError] = useState("");

  useEffect(() => {
  async function loadPage() {
    const accessToken = sessionStorage.getItem(ACCESS_TOKEN_KEY);

    if (!accessToken) {
      router.replace("/login");
      return;
    }

    try {
      setLoading(true);
      setError("");

      const assessmentResponse = await getAssessments(accessToken);
      setAssessments(assessmentResponse);

      try {
        const recommendationResponse =
          await getMyAssessmentRecommendations(accessToken);

        setResolvedCareerId(recommendationResponse.career_id);
        setRecommendations(recommendationResponse);
      } catch (recommendationError) {
        // The catalog remains usable when career recommendations are
        // unavailable or the student has not completed a mapped goal.
        setRecommendations(null);
        if (recommendationError instanceof ApiError && [401, 403].includes(recommendationError.status)) {
          setError(errorMessage(recommendationError, "Recommendations could not be loaded."));
        }
      }
    } catch (loadError) {
      setError(
        errorMessage(loadError, "Assessments could not be loaded.")
      );
    } finally {
      setLoading(false);
    }
  }

  void loadPage();
}, [router]);
  async function loadHistory(offset = 0) {
    const accessToken = sessionStorage.getItem(ACCESS_TOKEN_KEY);
    if (!accessToken) {
      router.replace("/login");
      return;
    }
    setShowHistory(true);
    setHistoryLoading(true);
    setHistoryError("");
    setHistoryOffset(offset);
    setAttempts(null);
    try {
      setAttempts(await getAssessmentAttempts(accessToken, offset));
    } catch (historyLoadError) {
      setHistoryError(errorMessage(historyLoadError, "Attempt history could not be loaded."));
    } finally {
      setHistoryLoading(false);
    }
  }

  async function openAttempt(attemptId: string) {
    if (openingGuard.current || submitGuard.current) return;
    const accessToken = sessionStorage.getItem(ACCESS_TOKEN_KEY);
    if (!accessToken) {
      router.replace("/login");
      return;
    }
    openingGuard.current = true;
    setOpeningId(attemptId);
    setError("");
    try {
      const persistedResult = await getAssessmentAttempt(accessToken, attemptId);
      setActiveAssessment(null);
      setResult(persistedResult);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (openError) {
      setError(errorMessage(openError, "Saved result could not be opened."));
    } finally {
      openingGuard.current = false;
      setOpeningId(null);
    }
  }

  async function handleOpenAssessment(assessmentId: string) {
    if (openingGuard.current || submitGuard.current) return;
    const accessToken = sessionStorage.getItem(ACCESS_TOKEN_KEY);

    if (!accessToken) {
      router.replace("/login");
      return;
    }

    openingGuard.current = true;
    try {
      setOpeningId(assessmentId);
      setError("");
      setResult(null);
      setAnswers({});
      setConfirming(false);

      const response = await getAssessment(
        accessToken,
        assessmentId
      );

      setActiveAssessment(response);
    } catch (openError) {
      setError(
        errorMessage(openError, "Assessment could not be opened.")
      );
    } finally {
      openingGuard.current = false;
      setOpeningId(null);
    }
  }

  function selectAnswer(
    questionId: string,
    selectedOption: string
  ) {
    if (submitGuard.current || confirming) return;
    setAnswers((current) => ({
      ...current,
      [questionId]: selectedOption,
    }));
  }

  async function handleSubmit(confirmed = false) {
    if (!activeAssessment || submitGuard.current || result) {
      return;
    }

    const unanswered = activeAssessment.questions.filter(
      (question) => !answers[question.id]
    );

    if (unanswered.length > 0) {
      setError(
        `Please answer all questions before submitting. ${unanswered.length} remaining.`
      );

      return;
    }

    const accessToken = sessionStorage.getItem(ACCESS_TOKEN_KEY);

    if (!accessToken) {
      router.replace("/login");
      return;
    }

    if (!confirmed) {
      setError("");
      setConfirming(true);
      return;
    }

    submitGuard.current = true;
    try {
      setSubmitting(true);
      setError("");

      const response = await submitAssessment(
        accessToken,
        activeAssessment.id,
        {
          answers: activeAssessment.questions.map((question) => ({
            question_id: question.id,
            selected_option: answers[question.id],
          })),
        }
      );

      setResult(response);
      setConfirming(false);
      setAttempts(null);
      setAssessments((current) => current.map((assessment) =>
        assessment.id === response.assessment_id
          ? { ...assessment, latest_attempt: response }
          : assessment
      ));

      try {
  if (resolvedCareerId) {
    const updatedRecommendations =
      await getMyAssessmentRecommendations(accessToken);

    setRecommendations(updatedRecommendations);
  }
} catch (refreshError) {
  // The assessment result remains valid even if refreshing
  // recommendations temporarily fails.
  setRecommendations(null);
  setError(errorMessage(refreshError, "Recommendations could not be refreshed. Your assessment result was saved."));
}

      window.scrollTo({
        top: 0,
        behavior: "smooth",
      });
    } catch (submitError) {
      const authenticationError = submitError instanceof ApiError && [401, 403].includes(submitError.status);
      setError(
        errorMessage(submitError, "Assessment could not be submitted.") +
        (authenticationError ? "" : " If the connection was interrupted, check Attempt History before retrying to avoid saving another attempt.")
      );
    } finally {
      submitGuard.current = false;
      setSubmitting(false);
    }
  }

  function resetAssessment() {
    if (submitGuard.current) return;
    setActiveAssessment(null);
    setResult(null);
    setAnswers({});
    setError("");
    setConfirming(false);
    if (showHistory) void loadHistory();
  }

  function renderRecommendationCard(
    recommendation: AssessmentRecommendation
  ) {
    return (
      <article
        key={recommendation.assessment_id}
        className="rounded-2xl border border-blue-200 bg-white p-6 shadow-sm"
      >
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex flex-wrap gap-2">
            <span className="rounded-full bg-blue-600 px-3 py-1 text-xs font-semibold text-white">
              Recommended
            </span>

            <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
              {recommendation.skill_name}
            </span>
          </div>

          <span className="text-xs font-medium text-slate-500">
            Version {recommendation.version}
          </span>
        </div>

        <h3 className="mt-5 text-xl font-bold text-slate-950">
          {recommendation.title}
        </h3>

        <p className="mt-3 text-sm leading-6 text-slate-600">
          {recommendation.description}
        </p>

        <div className="mt-5 rounded-xl border border-slate-200 bg-slate-50 p-4">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            {recommendation.competency ? "O*NET competency" : "O*NET technology signal"}
          </p>

          <p className="mt-2 font-semibold text-slate-950">
            {recommendation.competency?.element_name ?? recommendation.skill_name}
          </p>

          <div className="mt-2 flex flex-wrap gap-x-5 gap-y-2 text-xs text-slate-600">
            <span>
              {recommendation.competency?.skill_type ?? "Occupational signal, not a mandatory requirement"}
            </span>

            {recommendation.competency && recommendation.competency.importance !== null && (
              <span>
                Importance{" "}
                {recommendation.competency.importance.toFixed(2)}
              </span>
            )}

            {recommendation.competency && recommendation.competency.level !== null && (
              <span>
                Level {recommendation.competency.level.toFixed(2)}
              </span>
            )}
          </div>
        </div>

        <div className="mt-4 rounded-xl bg-blue-50 p-4">
          <p className="text-xs font-semibold uppercase tracking-wider text-blue-700">
            Why ACIF recommends this
          </p>

          <p className="mt-2 text-sm leading-6 text-slate-700">
            {recommendation.reason}
          </p>
        </div>

        <p className="mt-4 text-xs font-semibold uppercase tracking-wider text-slate-500">
          {formatDifficulty(recommendation.difficulty)}
        </p>

        <button
          type="button"
          disabled={openingId !== null}
          onClick={() =>
            handleOpenAssessment(recommendation.assessment_id)
          }
          className="mt-6 w-full rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {openingId === recommendation.assessment_id
            ? "Opening..."
            : "Start Recommended Assessment"}
        </button>
      </article>
    );
  }

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-50">
        <div className="text-center">
          <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-blue-600" />

          <p className="mt-4 text-sm text-slate-600">
            Loading technical assessments...
          </p>
        </div>
      </main>
    );
  }

  if (result) {
    return (
      <main className="min-h-screen bg-slate-50">
        <header className="border-b border-slate-200 bg-white">
          <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-5">
            <div>
              <p className="font-bold text-slate-950">
                CareerPilot AI
              </p>

              <p className="text-xs text-slate-500">
                Technical Assessment
              </p>
            </div>

            <button
              type="button"
              disabled={submitting}
              onClick={() => router.push("/dashboard")}
              className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700"
            >
              Dashboard
            </button>
          </div>
        </header>

        <div className="mx-auto max-w-5xl px-6 py-10">
          {error && <p role="alert" className="mb-6 rounded-xl bg-red-50 p-4 text-sm text-red-700">{error}</p>}
          <section className="rounded-3xl bg-slate-950 p-8 text-white">
            <p className="text-sm font-semibold uppercase tracking-wider text-blue-300">
              Saved assessment result
            </p>

            <h1 className="mt-3 text-3xl font-bold">
              {result.assessment_title}
            </h1>
            <p className="mt-3 text-sm text-slate-300">
              {result.skill_name} · Version {result.assessment_version} · Completed: {formatDate(result.completed_at)}
            </p>

            <div className="mt-7 grid gap-4 sm:grid-cols-3">
              <div className="rounded-2xl bg-white/10 p-5">
                <p className="text-sm text-slate-300">
                  Assessment score
                </p>

                <p className="mt-2 text-3xl font-bold">
                  {result.percentage === null ? "Not scored" : `${result.percentage.toFixed(0)}%`}
                </p>
              </div>

              <div className="rounded-2xl bg-white/10 p-5">
                <p className="text-sm text-slate-300">
                  Correct answers
                </p>

                <p className="mt-2 text-3xl font-bold">
                  {result.raw_score ?? "—"}/{result.total_questions ?? "—"}
                </p>
              </div>

              <div className="rounded-2xl bg-white/10 p-5">
                <p className="text-sm text-slate-300">
                  Status
                </p>

                <p className="mt-2 text-xl font-bold">
                  {result.status}
                </p>
              </div>
            </div>

            <p className="mt-6 text-sm leading-6 text-slate-300">
              This percentage represents your result on this
              specific assessment. It should not be interpreted as
              your overall {result.skill_name} proficiency.
            </p>
          </section>

          <section className="mt-8">
            <h2 className="text-2xl font-bold text-slate-950">
              Question review
            </h2>

            <p className="mt-2 text-sm text-slate-600">
              Review your answers and the explanation for each
              question.
            </p>
            {!activeAssessment && (
              <p className="mt-2 text-sm text-slate-600">
                Saved answers are shown by question ID; historical question text is not included in the saved result.
              </p>
            )}
            {result.answers.length === 0 && <p className="mt-4 text-sm text-slate-600">No saved answers are available for this attempt.</p>}

            <div className="mt-6 space-y-5">
              {result.answers.map(
                (answerResult, index) => {
                  const question = activeAssessment?.questions.find(
                    (item) => item.id === answerResult.question_id
                  );

                  return (
                    <article
                      key={answerResult.question_id}
                      className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                            Question {index + 1}
                          </p>

                          <h3 className="mt-2 font-semibold leading-6 text-slate-950">
                            {question?.question_text ?? `Question ID: ${answerResult.question_id}`}
                          </h3>
                        </div>

                        <span
                          className={`rounded-full px-3 py-1 text-xs font-semibold ${
                            answerResult.is_correct
                              ? "bg-emerald-50 text-emerald-700"
                              : "bg-red-50 text-red-700"
                          }`}
                        >
                          {answerResult.is_correct
                            ? "Correct"
                            : "Incorrect"}
                        </span>
                      </div>

                      <div className="mt-5 grid gap-3 sm:grid-cols-2">
                        <div className="rounded-xl bg-slate-50 p-4">
                          <p className="text-xs text-slate-500">
                            Your answer
                          </p>

                          <p className="mt-1 text-sm font-semibold text-slate-900">
                            {answerResult.selected_option}
                          </p>
                        </div>

                        <div className="rounded-xl bg-slate-50 p-4">
                          <p className="text-xs text-slate-500">
                            Correct answer
                          </p>

                          <p className="mt-1 text-sm font-semibold text-slate-900">
                            {answerResult.correct_option}
                          </p>
                        </div>
                      </div>

                      <div className="mt-4 rounded-xl border border-blue-100 bg-blue-50 p-4">
                        <p className="text-xs font-semibold uppercase tracking-wider text-blue-700">
                          Explanation
                        </p>

                        <p className="mt-2 text-sm leading-6 text-slate-700">
                            {answerResult.explanation ?? "No explanation available."}
                        </p>
                      </div>
                    </article>
                  );
                }
              )}
            </div>
          </section>

          <div className="mt-8 flex flex-wrap gap-3">
            <button
              type="button"
              disabled={submitting}
              onClick={resetAssessment}
              className="rounded-xl border border-slate-300 bg-white px-5 py-3 text-sm font-semibold text-slate-700"
            >
              Back to Assessments
            </button>

            <button
              type="button"
              disabled={submitting}
              onClick={() => router.push("/skills")}
              className="rounded-xl border border-blue-200 bg-blue-50 px-5 py-3 text-sm font-semibold text-blue-700"
            >
              View Skills & Evidence
            </button>

            <button
              type="button"
              disabled={submitting}
              onClick={() => router.push("/dashboard")}
              className="rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white"
            >
              View Updated Dashboard
            </button>
          </div>
        </div>
      </main>
    );
  }

  if (activeAssessment) {
    const answeredCount = activeAssessment.questions.filter(
      (question) => Boolean(answers[question.id])
    ).length;

    const progress =
      activeAssessment.questions.length > 0
        ? (answeredCount / activeAssessment.questions.length) * 100
        : 0;

    return (
      <main className="min-h-screen bg-slate-50">
        <header className="sticky top-0 z-20 border-b border-slate-200 bg-white">
          <div className="mx-auto max-w-4xl px-6 py-5">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="font-bold text-slate-950">
                  {activeAssessment.title}
                </p>

                <p className="mt-1 text-xs text-slate-500">
                  {answeredCount} of{" "}
                  {activeAssessment.questions.length} answered
                </p>
              </div>

              <button
                type="button"
                disabled={submitting}
                onClick={resetAssessment}
                className="text-sm font-semibold text-slate-600"
              >
                Exit
              </button>
            </div>

            <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-100">
              <div
                className="h-full rounded-full bg-blue-600 transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        </header>

        <div className="mx-auto max-w-4xl px-6 py-10">
          <div className="mb-8">
            <p className="text-sm font-semibold uppercase tracking-wider text-blue-600">
              {activeAssessment.skill_name} ·{" "}
              {formatDifficulty(activeAssessment.difficulty)}
            </p>

            <h1 className="mt-2 text-3xl font-bold text-slate-950">
              Technical Assessment
            </h1>

            <p className="mt-3 text-sm leading-6 text-slate-600">
              Select one answer for every question. Your result
              will be stored as assessment evidence in your
              CareerPilot profile.
            </p>
          </div>

          {error && (
            <div className="mb-6 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
              {error}
            </div>
          )}

          <div className="space-y-6">
            {activeAssessment.questions.map(
              (question, questionIndex) => (
                <article
                  key={question.id}
                  className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
                >
                  <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                    Question {questionIndex + 1}
                  </p>

                  <h2 className="mt-2 text-lg font-semibold leading-7 text-slate-950">
                    {question.question_text}
                  </h2>

                  <div className="mt-5 space-y-3">
                    {question.options.map((option) => {
                      const selected =
                        answers[question.id] === option.key;

                      return (
                        <button
                          key={option.key}
                          type="button"
                          disabled={submitting || confirming}
                          aria-pressed={selected}
                          onClick={() =>
                            selectAnswer(
                              question.id,
                              option.key
                            )
                          }
                          className={`flex w-full items-start gap-3 rounded-xl border p-4 text-left transition ${
                            selected
                              ? "border-blue-500 bg-blue-50 ring-2 ring-blue-100"
                              : "border-slate-200 bg-white hover:border-slate-300"
                          }`}
                        >
                          <span
                            className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                              selected
                                ? "bg-blue-600 text-white"
                                : "bg-slate-100 text-slate-700"
                            }`}
                          >
                            {option.key}
                          </span>

                          <span className="pt-0.5 text-sm leading-6 text-slate-700">
                            {option.text}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                </article>
              )
            )}
          </div>

          {confirming && (
            <section role="region" aria-labelledby="confirm-submit-title" className="mt-8 rounded-2xl border border-blue-200 bg-blue-50 p-6">
              <h2 id="confirm-submit-title" className="font-semibold text-slate-950">Submit this assessment?</h2>
              <p className="mt-2 text-sm text-slate-700">All {answeredCount} answers will be submitted and saved as a new attempt. Submitted answers cannot be changed.</p>
              <div className="mt-4 flex gap-3">
                <button type="button" disabled={submitting} onClick={() => setConfirming(false)} className="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-semibold disabled:opacity-60">Keep reviewing</button>
                <button type="button" disabled={submitting} onClick={() => void handleSubmit(true)} className="rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60">{submitting ? "Submitting..." : "Confirm submission"}</button>
              </div>
            </section>
          )}
          <button
            type="button"
            disabled={submitting || confirming}
            onClick={() => void handleSubmit()}
            className="mt-8 w-full rounded-xl bg-blue-600 px-6 py-4 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {submitting
              ? "Submitting assessment..."
              : `Submit Assessment (${answeredCount}/${activeAssessment.questions.length})`}
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
          <div>
            <p className="font-bold text-slate-950">
              CareerPilot AI
            </p>

            <p className="text-xs text-slate-500">
              Evidence-Aware Career Intelligence
            </p>
          </div>

          <button
            type="button"
            onClick={() => router.push("/dashboard")}
            className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700"
          >
            Back to Dashboard
          </button>
        </div>
      </header>

      <div className="mx-auto max-w-6xl px-6 py-10">
        <p className="text-sm font-semibold uppercase tracking-wider text-blue-600">
          Evidence Verification
        </p>

        <h1 className="mt-2 text-3xl font-bold text-slate-950">
          Technical Assessments
        </h1>

        <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
          Assessments provide measured evidence that is kept
          separate from resume claims and project detections.
          Results contribute evidence to your Career Twin without
          being treated as complete proof of skill proficiency.
        </p>

        {error && (
          <div className="mt-6 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            {error}
          </div>
        )}

        <nav aria-label="Assessment views" className="mt-6 flex gap-3">
          <button type="button" aria-pressed={!showHistory} disabled={openingId !== null} onClick={() => setShowHistory(false)} className="rounded-xl border border-slate-300 bg-white px-5 py-3 text-sm font-semibold text-slate-700">Assessment Catalog</button>
          <button type="button" aria-pressed={showHistory} disabled={historyLoading || openingId !== null} onClick={() => void loadHistory()} className="rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white disabled:opacity-60">Attempt History</button>
        </nav>

        {showHistory && (
          <section className="mt-8" aria-labelledby="history-title">
            <h2 id="history-title" className="text-2xl font-bold text-slate-950">Your assessment attempts</h2>
            {historyLoading ? <p role="status" className="mt-4 text-slate-600">Loading attempt history...</p> : historyError ? (
              <div role="alert" className="mt-4 rounded-xl bg-red-50 p-4 text-red-700">
                <p>{historyError}</p>
                <button type="button" onClick={() => void loadHistory(historyOffset)} className="mt-3 font-semibold underline">Retry history</button>
              </div>
            ) : attempts !== null ? (
              attempts.length === 0 ? <p className="mt-4 rounded-xl bg-white p-6 text-slate-600">{historyOffset === 0 ? "You have no saved assessment attempts yet." : "No more assessment attempts on this page."}</p> : (
                <div className="mt-5 space-y-4">
                  {attempts.map((attempt) => (
                    <article key={attempt.attempt_id} className="rounded-2xl border border-slate-200 bg-white p-6">
                      <h3 className="text-lg font-bold text-slate-950">{attempt.assessment_title}</h3>
                      <p className="mt-2 text-sm text-slate-600">{attempt.skill_name} · Version {attempt.assessment_version} · {attempt.status}</p>
                      <p className="mt-2 text-sm text-slate-700">Assessment score: {attempt.percentage === null ? "Not scored" : `${attempt.percentage.toFixed(0)}%`} · Correct answers: {attempt.raw_score ?? "—"}/{attempt.total_questions ?? "—"}</p>
                      <p className="mt-2 text-xs text-slate-500">Started: {formatDate(attempt.started_at)} · Completed: {formatDate(attempt.completed_at)}</p>
                      <button type="button" disabled={openingId !== null} onClick={() => void openAttempt(attempt.attempt_id)} className="mt-4 rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-60">{openingId === attempt.attempt_id ? "Opening..." : "View saved result"}</button>
                    </article>
                  ))}
                </div>
              )
            ) : <button type="button" onClick={() => void loadHistory()} className="mt-4 font-semibold text-blue-700 underline">Load attempt history</button>}
            <div className="mt-5 flex items-center gap-4 text-sm">
              <button type="button" disabled={historyLoading || openingId !== null || historyOffset === 0} onClick={() => void loadHistory(Math.max(0, historyOffset - 50))} className="font-semibold text-blue-700 disabled:opacity-40">Previous attempts</button>
              <span className="text-slate-600">Page {Math.floor(historyOffset / 50) + 1}</span>
              <button type="button" disabled={historyLoading || openingId !== null || attempts?.length !== 50} onClick={() => void loadHistory(historyOffset + 50)} className="font-semibold text-blue-700 disabled:opacity-40">More attempts</button>
            </div>
          </section>
        )}

        {!showHistory && recommendations && (
          <section className="mt-10">
            <div className="rounded-3xl bg-slate-950 p-7 text-white">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-semibold uppercase tracking-wider text-blue-300">
                    ACIF Recommendations
                  </p>

                  <h2 className="mt-2 text-2xl font-bold">
                    Recommended for your target career
                  </h2>

                  <p className="mt-2 text-sm text-slate-300">
                    O*NET anchor: {recommendations.career_title} ·{" "}
                    {recommendations.onet_soc_code}
                  </p>
                </div>

                <div className="rounded-2xl bg-white/10 px-5 py-3 text-center">
                  <p className="text-2xl font-bold">
                    {recommendations.recommended_count}
                  </p>

                  <p className="text-xs text-slate-300">
                    Recommended
                  </p>
                </div>
              </div>

              <p className="mt-5 max-w-4xl text-sm leading-6 text-slate-300">
                ACIF compares occupational competencies with
                assessment-derived measurements in your current
                Career Twin. Recommendations appear when a mapped
                competency still needs measurement.
              </p>
            </div>

            {recommendations.recommendations.length > 0 ? (
              <div className="mt-5 grid gap-5 md:grid-cols-2">
                {recommendations.recommendations.map(
                  renderRecommendationCard
                )}
              </div>
            ) : (
              <div className="mt-5 rounded-2xl border border-emerald-200 bg-emerald-50 p-6">
                <h3 className="font-semibold text-emerald-900">
                  No mapped assessments currently recommended
                </h3>

                <p className="mt-2 max-w-3xl text-sm leading-6 text-emerald-800">
                  Your current Career Twin already contains
                  assessment-derived measurements for the active
                  assessments that are mapped to competencies for
                  this occupational anchor. More recommendations
                  can appear as CareerPilot adds additional mapped
                  assessments.
                </p>
              </div>
            )}
          </section>
        )}

        {!showHistory && <section className="mt-12">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wider text-slate-500">
              Assessment Catalog
            </p>

            <h2 className="mt-2 text-2xl font-bold text-slate-950">
              All Assessments
            </h2>

            <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
              Browse all active CareerPilot assessments. An
              assessment can remain available here even when ACIF
              no longer recommends it for your current competency
              gaps.
            </p>
          </div>

          {assessments.length === 0 ? (
            <div className="mt-6 rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center">
              <h3 className="font-semibold text-slate-900">
                No assessments available
              </h3>

              <p className="mt-2 text-sm text-slate-500">
                New technical assessments will appear here when
                available.
              </p>
            </div>
          ) : (
            <div className="mt-6 grid gap-5 md:grid-cols-2">
              {assessments.map((assessment) => (
                <article
                  key={assessment.id}
                  className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
                >
                  <div className="flex items-start justify-between gap-4">
                    <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
                      {assessment.skill_name}
                    </span>

                    <span className="text-xs font-medium text-slate-500">
                      Version {assessment.version}
                    </span>
                  </div>

                  <h3 className="mt-5 text-xl font-bold text-slate-950">
                    {assessment.title}
                  </h3>

                  <p className="mt-3 text-sm leading-6 text-slate-600">
                    {assessment.description}
                  </p>

                  <p className="mt-4 text-xs font-semibold uppercase tracking-wider text-slate-500">
                    {formatDifficulty(assessment.difficulty)} · {assessment.question_count} questions
                  </p>
                  <p className="mt-3 text-sm text-slate-600">
                    {assessment.latest_attempt
                      ? `Attempted · ${assessment.latest_attempt.status} · Latest assessment score: ${assessment.latest_attempt.percentage === null ? "Not scored" : `${assessment.latest_attempt.percentage.toFixed(0)}%`}`
                      : "Not attempted"}
                  </p>
                  {assessment.latest_attempt && (
                    <button type="button" disabled={openingId !== null} onClick={() => void openAttempt(assessment.latest_attempt!.attempt_id)} className="mt-3 text-sm font-semibold text-blue-700 underline disabled:opacity-60">View latest saved result</button>
                  )}

                  <button
                    type="button"
                    disabled={openingId !== null}
                    onClick={() =>
                      handleOpenAssessment(assessment.id)
                    }
                    className="mt-6 w-full rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {openingId === assessment.id
                      ? "Opening..."
                      : assessment.latest_attempt ? "Retake Assessment" : "Start Assessment"}
                  </button>
                </article>
              ))}
            </div>
          )}
        </section>}
      </div>
    </main>
  );
}
