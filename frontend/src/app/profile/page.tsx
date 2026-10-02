"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import {
  createStudentProfile,
  getStudentProfile,
  updateStudentProfile,
  getCareerGoals,
  updateCareerGoal,
  getEducations,
  getExperiences,
  getProjects,
  getCertifications,
  type StudentProfile,
  type StudentProfileData,
  type CareerGoal,
  type Education,
  type Experience,
  type Project,
  type Certification,
} from "@/lib/api/students";
import EducationSection from "@/components/profile/EducationSection";
import ExperienceSection from "@/components/profile/ExperienceSection";
import ProjectSection from "@/components/profile/ProjectSection";
import CertificationSection from "@/components/profile/CertificationSection";
const ACCESS_TOKEN_KEY = "careerpilot_access_token";

export default function ProfilePage() {
  const router = useRouter();

  const [profile, setProfile] =
    useState<StudentProfile | null>(null);

  const [careerGoals, setCareerGoals] =
    useState<CareerGoal[]>([]);
  const [educations, setEducations] =
  useState<Education[]>([]);

const [experiences, setExperiences] =
  useState<Experience[]>([]);

const [projects, setProjects] =
  useState<Project[]>([]);

const [certifications, setCertifications] =
  useState<Certification[]>([]);

const [accessToken, setAccessToken] =
  useState<string | null>(null);
  const [form, setForm] =
    useState<StudentProfileData>({
      full_name: "",
      phone: "",
      city: "",
      state: "",
      country: "",
      headline: "",
      bio: "",
    });

  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [changingGoalId, setChangingGoalId] =
    useState<string | null>(null);

  const [error, setError] =
    useState<string | null>(null);

  const [message, setMessage] =
    useState<string | null>(null);

  useEffect(() => {
  async function loadProfile() {
    const accessToken =
      sessionStorage.getItem(ACCESS_TOKEN_KEY);

    if (!accessToken) {
      router.replace("/login");
      return;
    }
     setAccessToken(accessToken);

  
    try {
      setIsLoading(true);
      setError(null);

      // Career goals must load independently.
      
       const [
  goalsResponse,
  educationsResponse,
  experiencesResponse,
  projectsResponse,
  certificationsResponse,
] = await Promise.all([
  getCareerGoals(accessToken),
  getEducations(accessToken),
  getExperiences(accessToken),
  getProjects(accessToken),
  getCertifications(accessToken),
]);

setCareerGoals(goalsResponse);
setEducations(educationsResponse);
setExperiences(experiencesResponse);
setProjects(projectsResponse);
setCertifications(certificationsResponse);

      // Profile may not exist yet for a new/fresh account.
      try {
        const profileResponse =
          await getStudentProfile(accessToken);

        setProfile(profileResponse);

        setForm({
          full_name: profileResponse.full_name,
          phone: profileResponse.phone ?? "",
          city: profileResponse.city ?? "",
          state: profileResponse.state ?? "",
          country: profileResponse.country ?? "",
          headline: profileResponse.headline ?? "",
          bio: profileResponse.bio ?? "",
        });
      } catch (profileError) {
        console.info(
          "Student profile has not been created yet.",
          profileError,
        );

        setProfile(null);

        setForm({
          full_name: "",
          phone: "",
          city: "",
          state: "",
          country: "",
          headline: "",
          bio: "",
        });
      }
    } catch (err) {
      console.error(
        "Profile page loading failed:",
        err,
      );

      setError(
        err instanceof Error
          ? err.message
          : "Unable to load your career profile.",
      );
    } finally {
      setIsLoading(false);
    }
  }

  void loadProfile();
}, [router]);

  function updateField(
    field: keyof StudentProfileData,
    value: string,
  ) {
    setForm((current) => ({
      ...current,
      [field]: value,
    }));
  }

  async function handleSaveProfile() {
    const accessToken =
      sessionStorage.getItem(ACCESS_TOKEN_KEY);

    if (!accessToken) {
      router.replace("/login");
      return;
    }

    if (!form.full_name.trim()) {
      setError("Full name is required.");
      return;
    }

    try {
      setIsSaving(true);
      setError(null);
      setMessage(null);

      const profileData = {
  ...form,
  full_name: form.full_name.trim(),
};

      const updatedProfile = profile
  ? await updateStudentProfile(
      accessToken,
      profileData,
    )
  : await createStudentProfile(
      accessToken,
      profileData,
    );

      setProfile(updatedProfile);
      setMessage("Profile updated successfully.");
    } catch (err) {
      console.error("Profile update failed:", err);

      setError(
        err instanceof Error
          ? err.message
          : "Unable to update your profile.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  async function handleMakePrimary(
    careerGoal: CareerGoal,
  ) {
    const accessToken =
      sessionStorage.getItem(ACCESS_TOKEN_KEY);

    if (!accessToken) {
      router.replace("/login");
      return;
    }

    if (careerGoal.is_primary) {
      return;
    }

    try {
      setChangingGoalId(careerGoal.id);
      setError(null);
      setMessage(null);

      await updateCareerGoal(
        accessToken,
        careerGoal.id,
        {
          is_primary: true,
          is_active: true,
        },
      );

      const refreshedGoals =
        await getCareerGoals(accessToken);

      setCareerGoals(refreshedGoals);

      setMessage(
        `${careerGoal.target_role} is now your primary target career.`,
      );
    } catch (err) {
      console.error(
        "Primary career update failed:",
        err,
      );

      setError(
        err instanceof Error
          ? err.message
          : "Unable to change your primary career.",
      );
    } finally {
      setChangingGoalId(null);
    }
  }

  if (isLoading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-50">
        <div className="text-center">
          <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-blue-600" />

          <p className="mt-4 text-sm text-slate-600">
            Loading your profile...
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
          <button
            type="button"
            onClick={() => router.push("/dashboard")}
            className="text-left"
          >
            <p className="text-xl font-bold text-slate-950">
              CareerPilot AI
            </p>

            <p className="text-xs text-slate-500">
              Adaptive Career Intelligence
            </p>
          </button>

          <button
            type="button"
            onClick={() => router.push("/dashboard")}
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
          >
            Dashboard
          </button>
        </div>
      </header>

      <div className="mx-auto max-w-6xl px-6 py-10">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wider text-blue-600">
            Student Profile
          </p>

          <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-950">
            Your Career Profile
          </h1>

          <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-600">
            Manage the information CareerPilot uses to
            understand your background and career direction.
          </p>
        </div>

        {error && (
          <div className="mt-6 rounded-xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
            {error}
          </div>
        )}

        {message && (
          <div className="mt-6 rounded-xl border border-emerald-200 bg-emerald-50 px-5 py-4 text-sm text-emerald-700">
            {message}
          </div>
        )}

        <section className="mt-8 rounded-3xl border border-slate-200 bg-white p-7 shadow-sm">
          <div>
            <p className="text-sm font-semibold uppercase tracking-wider text-blue-600">
              Personal Information
            </p>

            <h2 className="mt-2 text-2xl font-bold text-slate-950">
              Profile
            </h2>
          </div>

          <div className="mt-7 grid gap-5 md:grid-cols-2">
            <Field
              label="Full name"
              value={form.full_name}
              onChange={(value) =>
                updateField("full_name", value)
              }
            />

            <Field
              label="Phone"
              value={form.phone ?? ""}
              onChange={(value) =>
                updateField("phone", value)
              }
            />

            <Field
              label="City"
              value={form.city ?? ""}
              onChange={(value) =>
                updateField("city", value)
              }
            />

            <Field
              label="State"
              value={form.state ?? ""}
              onChange={(value) =>
                updateField("state", value)
              }
            />

            <Field
              label="Country"
              value={form.country ?? ""}
              onChange={(value) =>
                updateField("country", value)
              }
            />

            <Field
              label="Professional headline"
              value={form.headline ?? ""}
              onChange={(value) =>
                updateField("headline", value)
              }
            />
          </div>

          <div className="mt-5">
            <label className="text-sm font-medium text-slate-700">
              Bio
            </label>

            <textarea
              value={form.bio ?? ""}
              onChange={(event) =>
                updateField(
                  "bio",
                  event.target.value,
                )
              }
              rows={5}
              className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              placeholder="Tell CareerPilot about your interests, goals, and background."
            />
          </div>

          <div className="mt-6 flex justify-end">
            <button
              type="button"
              disabled={isSaving}
              onClick={handleSaveProfile}
              className="rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSaving
                ? "Saving..."
                : "Save Profile"}
            </button>
          </div>
        </section>

        <section className="mt-8 rounded-3xl border border-slate-200 bg-white p-7 shadow-sm">
          <p className="text-sm font-semibold uppercase tracking-wider text-blue-600">
            Career Direction
          </p>

          <h2 className="mt-2 text-2xl font-bold text-slate-950">
            Career Goals
          </h2>

          <p className="mt-3 text-sm leading-6 text-slate-600">
            Your primary target drives ACIF gap analysis,
            readiness dimensions, Career GPS and adaptive
            recommendations.
          </p>

          {careerGoals.length === 0 ? (
            <div className="mt-6 rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-6">
              <p className="font-semibold text-slate-900">
                No career goals yet
              </p>

              <p className="mt-2 text-sm text-slate-600">
                Complete career discovery to establish your
                first target career.
              </p>

              <button
                type="button"
                onClick={() =>
                  router.push(
                    "/assessment/riasec/results",
                  )
                }
                className="mt-4 rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white"
              >
                Explore Careers
              </button>
            </div>
          ) : (
            <div className="mt-6 space-y-4">
              {careerGoals.map((goal) => (
                <article
                  key={goal.id}
                  className={`rounded-2xl border p-5 ${
                    goal.is_primary
                      ? "border-blue-300 bg-blue-50/50"
                      : "border-slate-200"
                  }`}
                >
                  <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="text-lg font-semibold text-slate-950">
                          {goal.target_role}
                        </h3>

                        {goal.is_primary && (
                          <span className="rounded-full bg-blue-600 px-3 py-1 text-xs font-semibold text-white">
                            Primary Target
                          </span>
                        )}

                        {!goal.is_active && (
                          <span className="rounded-full bg-slate-200 px-3 py-1 text-xs font-semibold text-slate-600">
                            Inactive
                          </span>
                        )}
                      </div>

                      <p className="mt-2 text-sm text-slate-600">
                        O*NET SOC:{" "}
                        {goal.onet_soc_code ??
                          "Not mapped"}
                      </p>

                      {goal.target_industry && (
                        <p className="mt-1 text-sm text-slate-500">
                          Industry:{" "}
                          {goal.target_industry}
                        </p>
                      )}

                      {goal.target_timeline_months && (
                        <p className="mt-1 text-sm text-slate-500">
                          Target timeline:{" "}
                          {
                            goal.target_timeline_months
                          }{" "}
                          months
                        </p>
                      )}
                    </div>

                    {!goal.is_primary && (
                      <button
                        type="button"
                        disabled={
                          changingGoalId === goal.id
                        }
                        onClick={() =>
                          handleMakePrimary(goal)
                        }
                        className="rounded-xl border border-blue-200 bg-white px-4 py-2.5 text-sm font-semibold text-blue-700 transition hover:bg-blue-50 disabled:opacity-60"
                      >
                        {changingGoalId === goal.id
                          ? "Updating..."
                          : "Make Primary"}
                      </button>
                    )}
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
        {accessToken && (
  <>
    <EducationSection
      accessToken={accessToken}
      educations={educations}
      onChange={setEducations}
      onMessage={(value) => {
        setError(null);
        setMessage(value);
      }}
      onError={(value) => {
        setMessage(null);
        setError(value);
      }}
    />

    <ExperienceSection
      accessToken={accessToken}
      experiences={experiences}
      onChange={setExperiences}
      onMessage={(value) => {
        setError(null);
        setMessage(value);
      }}
      onError={(value) => {
        setMessage(null);
        setError(value);
      }}
    />

    <ProjectSection
      accessToken={accessToken}
      projects={projects}
      onChange={setProjects}
      onMessage={(value) => {
        setError(null);
        setMessage(value);
      }}
      onError={(value) => {
        setMessage(null);
        setError(value);
      }}
    />

    <CertificationSection
      accessToken={accessToken}
      certifications={certifications}
      onChange={setCertifications}
      onMessage={(value) => {
        setError(null);
        setMessage(value);
      }}
      onError={(value) => {
        setMessage(null);
        setError(value);
      }}
    />
  </>
)}
        <section className="mt-8 rounded-2xl border border-slate-200 bg-slate-100 p-5">
          <p className="text-sm font-semibold text-slate-900">
            Career Twin integration
          </p>

          <p className="mt-2 text-sm leading-6 text-slate-600">
            Changing your primary target updates the career
            state used by CareerPilot. ACIF then evaluates
            your current evidence against the newly selected
            occupational target.
          </p>
        </section>
      </div>
    </main>
  );
}

function Field({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div>
      <label className="text-sm font-medium text-slate-700">
        {label}
      </label>

      <input
        type="text"
        value={value}
        onChange={(event) =>
          onChange(event.target.value)
        }
        className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
      />
    </div>
  );
}