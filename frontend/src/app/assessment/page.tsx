"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import {
  AssessmentDetail,
  AssessmentRecommendation,
  AssessmentSubmissionResponse,
  AssessmentSummary,
  CareerAssessmentRecommendationsResponse,
  getAssessment,
  getAssessments,
  getCareerAssessmentRecommendations,
  submitAssessment,
} from "@/lib/api/assessments";
import {
  getPrimaryCareerGoal,
} from "@/lib/api/students";

import {
  resolveCareerByOnetCode,
} from "@/lib/api/careers";
const ACCESS_TOKEN_KEY = "careerpilot_access_token";



type Answers = Record<string, string>;

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

      const [assessmentResponse, primaryGoal] = await Promise.all([
        getAssessments(accessToken),
        getPrimaryCareerGoal(accessToken),
      ]);

      if (!primaryGoal.onet_soc_code) {
        throw new Error(
          "Your primary career goal does not have an O*NET occupation mapping."
        );
      }

      const targetCareer = await resolveCareerByOnetCode(
        primaryGoal.target_role,
        primaryGoal.onet_soc_code
      );

      const careerId = targetCareer.id;

      const recommendationResponse =
        await getCareerAssessmentRecommendations(
          accessToken,
          careerId
        );

      setAssessments(assessmentResponse);
      setResolvedCareerId(careerId);
      setRecommendations(recommendationResponse);
    } catch (loadError) {
      setError(
        loadError instanceof Error
          ? loadError.message
          : "Assessments could not be loaded."
      );
    } finally {
      setLoading(false);
    }
  }

  void loadPage();
}, [router]);
  async function handleOpenAssessment(assessmentId: string) {
    const accessToken = sessionStorage.getItem(ACCESS_TOKEN_KEY);

    if (!accessToken) {
      router.replace("/login");
      return;
    }

    try {
      setOpeningId(assessmentId);
      setError("");
      setResult(null);
      setAnswers({});

      const response = await getAssessment(
        accessToken,
        assessmentId
      );

      setActiveAssessment(response);
    } catch (openError) {
      setError(
        openError instanceof Error
          ? openError.message
          : "Assessment could not be opened."
      );
    } finally {
      setOpeningId(null);
    }
  }

  function selectAnswer(
    questionId: string,
    selectedOption: string
  ) {
    setAnswers((current) => ({
      ...current,
      [questionId]: selectedOption,
    }));
  }

  async function handleSubmit() {
    if (!activeAssessment) {
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

      try {
  if (resolvedCareerId) {
    const updatedRecommendations =
      await getCareerAssessmentRecommendations(
        accessToken,
        resolvedCareerId
      );

    setRecommendations(updatedRecommendations);
  }
} catch {
  // The assessment result remains valid even if refreshing
  // recommendations temporarily fails.
}

      window.scrollTo({
        top: 0,
        behavior: "smooth",
      });
    } catch (submitError) {
      setError(
        submitError instanceof Error
          ? submitError.message
          : "Assessment could not be submitted."
      );
    } finally {
      setSubmitting(false);
    }
  }

  function resetAssessment() {
    setActiveAssessment(null);
    setResult(null);
    setAnswers({});
    setError("");
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
            O*NET competency
          </p>

          <p className="mt-2 font-semibold text-slate-950">
            {recommendation.competency.element_name}
          </p>

          <div className="mt-2 flex flex-wrap gap-x-5 gap-y-2 text-xs text-slate-600">
            <span>
              {recommendation.competency.skill_type}
            </span>

            {recommendation.competency.importance !== null && (
              <span>
                Importance{" "}
                {recommendation.competency.importance.toFixed(2)}
              </span>
            )}

            {recommendation.competency.level !== null && (
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

  if (result && activeAssessment) {
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
              onClick={() => router.push("/dashboard")}
              className="rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700"
            >
              Dashboard
            </button>
          </div>
        </header>

        <div className="mx-auto max-w-5xl px-6 py-10">
          <section className="rounded-3xl bg-slate-950 p-8 text-white">
            <p className="text-sm font-semibold uppercase tracking-wider text-blue-300">
              Assessment completed
            </p>

            <h1 className="mt-3 text-3xl font-bold">
              {activeAssessment.title}
            </h1>

            <div className="mt-7 grid gap-4 sm:grid-cols-3">
              <div className="rounded-2xl bg-white/10 p-5">
                <p className="text-sm text-slate-300">
                  Assessment score
                </p>

                <p className="mt-2 text-3xl font-bold">
                  {result.percentage.toFixed(0)}%
                </p>
              </div>

              <div className="rounded-2xl bg-white/10 p-5">
                <p className="text-sm text-slate-300">
                  Correct answers
                </p>

                <p className="mt-2 text-3xl font-bold">
                  {result.raw_score}/{result.total_questions}
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

            <div className="mt-6 space-y-5">
              {activeAssessment.questions.map(
                (question, index) => {
                  const answerResult = result.answers.find(
                    (item) => item.question_id === question.id
                  );

                  if (!answerResult) {
                    return null;
                  }

                  return (
                    <article
                      key={question.id}
                      className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                            Question {index + 1}
                          </p>

                          <h3 className="mt-2 font-semibold leading-6 text-slate-950">
                            {question.question_text}
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
                          {answerResult.explanation}
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
              onClick={resetAssessment}
              className="rounded-xl border border-slate-300 bg-white px-5 py-3 text-sm font-semibold text-slate-700"
            >
              Back to Assessments
            </button>

            <button
              type="button"
              onClick={() => router.push("/skills")}
              className="rounded-xl border border-blue-200 bg-blue-50 px-5 py-3 text-sm font-semibold text-blue-700"
            >
              View Skills & Evidence
            </button>

            <button
              type="button"
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

          <button
            type="button"
            disabled={submitting}
            onClick={handleSubmit}
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

        {recommendations && (
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

        <section className="mt-12">
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
                    {formatDifficulty(assessment.difficulty)}
                  </p>

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
                      : "Start Assessment"}
                  </button>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}