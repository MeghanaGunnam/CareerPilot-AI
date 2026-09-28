"use client";

import {
  FormEvent,
  useEffect,
  useState,
} from "react";
import { useRouter } from "next/navigation";

import CertificationStep from "@/components/onboarding/CertificationStep";
import CareerGoalStep from "@/components/onboarding/CareerGoalStep";
import ExperienceStep from "@/components/onboarding/ExperienceStep";
import ProjectStep from "@/components/onboarding/ProjectStep";

import { ApiError } from "@/lib/api/client";

import {
  createEducation,
  createStudentProfile,
  getCareerGoals,
  getCertifications,
  getEducations,
  getExperiences,
  getProjects,
  getStudentProfile,
  updateStudentProfile,
  type CareerGoal,
  type Certification,
  type Education,
  type EducationData,
  type Experience,
  type Project,
  type StudentProfile,
  type StudentProfileData,
} from "@/lib/api/students";

const steps = [
  "Profile",
  "Education",
  "Experience",
  "Projects",
  "Certifications",
  "Career Goal",
];

export default function OnboardingPage() {
  const router = useRouter();

  const [accessToken, setAccessToken] =
    useState("");

  const [currentStep, setCurrentStep] =
    useState(0);

  const [isLoading, setIsLoading] =
    useState(true);

  const [isSaving, setIsSaving] =
    useState(false);

  const [error, setError] = useState("");

  const [
    existingProfile,
    setExistingProfile,
  ] = useState<StudentProfile | null>(null);

  const [educations, setEducations] =
    useState<Education[]>([]);

  const [experiences, setExperiences] =
    useState<Experience[]>([]);

  const [projects, setProjects] =
    useState<Project[]>([]);

  const [
    certifications,
    setCertifications,
  ] = useState<Certification[]>([]);

  const [careerGoals, setCareerGoals] =
    useState<CareerGoal[]>([]);

  const [profileData, setProfileData] =
    useState<StudentProfileData>({
      full_name: "",
      phone: "",
      city: "",
      state: "",
      country: "",
      headline: "",
      bio: "",
    });

  const [educationData, setEducationData] =
    useState<EducationData>({
      institution_name: "",
      degree: "",
      field_of_study: "",
      start_year: undefined,
      end_year: undefined,
      grade: "",
    });

  useEffect(() => {
    const token = sessionStorage.getItem(
      "careerpilot_access_token"
    );

    if (!token) {
      router.replace("/login");
      return;
    }

    

    async function loadOnboarding() {
      try {
        setAccessToken(token!);
        const profile =
          await getStudentProfile(token!);

        setExistingProfile(profile);

        setProfileData({
          full_name: profile.full_name ?? "",
          phone: profile.phone ?? "",
          city: profile.city ?? "",
          state: profile.state ?? "",
          country: profile.country ?? "",
          headline: profile.headline ?? "",
          bio: profile.bio ?? "",
        });

        const [
          educationRecords,
          experienceRecords,
          projectRecords,
          certificationRecords,
          careerGoalRecords,
        ] = await Promise.all([
          getEducations(token!),
          getExperiences(token!),
          getProjects(token!),
          getCertifications(token!),
          getCareerGoals(token!),
        ]);

        setEducations(educationRecords);
        setExperiences(experienceRecords);
        setProjects(projectRecords);
        setCertifications(
          certificationRecords
        );
        setCareerGoals(careerGoalRecords);

        /*
         * Education is required for our
         * onboarding foundation.
         *
         * Experience and certifications are
         * optional, so their absence cannot be
         * used to infer whether the student has
         * already visited those steps.
         *
         * For the current V1, once education
         * exists we continue at Experience.
         * During the same browser session,
         * navigation proceeds normally through
         * all remaining steps.
         */
        if (educationRecords.length === 0) {
          setCurrentStep(1);
        } else if (
          careerGoalRecords.length > 0
        ) {
          setCurrentStep(5);
        } else {
          setCurrentStep(2);
        }
      } catch (loadError) {
        if (
          loadError instanceof ApiError &&
          loadError.status === 404
        ) {
          setCurrentStep(0);
        } else if (
          loadError instanceof ApiError &&
          loadError.status === 401
        ) {
          clearAuthentication();
          router.replace("/login");
          return;
        } else {
          setError(
            "Unable to load your onboarding information."
          );
        }
      } finally {
        setIsLoading(false);
      }
    }

    loadOnboarding();
  }, [router]);

  function clearAuthentication() {
    sessionStorage.removeItem(
      "careerpilot_access_token"
    );

    sessionStorage.removeItem(
      "careerpilot_refresh_token"
    );
  }

  function updateProfileField(
    field: keyof StudentProfileData,
    value: string
  ) {
    setProfileData((current) => ({
      ...current,
      [field]: value,
    }));
  }

  function updateEducationField(
    field: keyof EducationData,
    value: string | number | undefined
  ) {
    setEducationData((current) => ({
      ...current,
      [field]: value,
    }));
  }

  async function handleProfileSubmit(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    setError("");

    if (!accessToken) {
      router.replace("/login");
      return;
    }

    setIsSaving(true);

    try {
      let savedProfile: StudentProfile;

      if (existingProfile) {
        savedProfile =
          await updateStudentProfile(
            accessToken,
            profileData
          );
      } else {
        savedProfile =
          await createStudentProfile(
            accessToken,
            profileData
          );
      }

      setExistingProfile(savedProfile);
      setCurrentStep(1);
    } catch (saveError) {
      handleRequestError(
        saveError,
        "Unable to save your profile."
      );
    } finally {
      setIsSaving(false);
    }
  }

  async function handleEducationSubmit(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    setError("");

    if (!accessToken) {
      router.replace("/login");
      return;
    }

    setIsSaving(true);

    try {
      const savedEducation =
        await createEducation(
          accessToken,
          educationData
        );

      setEducations((current) => [
        ...current,
        savedEducation,
      ]);

      setEducationData({
        institution_name: "",
        degree: "",
        field_of_study: "",
        start_year: undefined,
        end_year: undefined,
        grade: "",
      });
    } catch (saveError) {
      handleRequestError(
        saveError,
        "Unable to save your education."
      );
    } finally {
      setIsSaving(false);
    }
  }

  function handleRequestError(
    requestError: unknown,
    fallbackMessage: string
  ) {
    if (
      requestError instanceof ApiError
    ) {
      if (requestError.status === 401) {
        clearAuthentication();
        router.replace("/login");
        return;
      }

      setError(requestError.message);
      return;
    }

    setError(fallbackMessage);
  }

  if (isLoading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-50">
        <div className="text-center">
          <div className="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-slate-900" />

          <p className="mt-4 text-slate-600">
            Preparing your CareerPilot
            profile...
          </p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
          <div>
            <p className="text-xl font-bold text-slate-950">
              CareerPilot AI
            </p>

            <p className="mt-1 text-sm text-slate-500">
              Career Intelligence Onboarding
            </p>
          </div>

          <button
            type="button"
            onClick={() =>
              router.push("/dashboard")
            }
            className="text-sm font-medium text-slate-600 hover:text-slate-950"
          >
            Exit onboarding
          </button>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-6 py-10">
        <div className="grid gap-10 lg:grid-cols-[280px_1fr]">
          <aside>
            <p className="text-sm font-semibold uppercase tracking-wider text-blue-600">
              Your Career Twin
            </p>

            <h1 className="mt-2 text-2xl font-semibold text-slate-950">
              Build your foundation
            </h1>

            <p className="mt-3 text-sm leading-6 text-slate-600">
              Add the information CareerPilot
              needs to understand your current
              career state.
            </p>

            <div className="mt-8 space-y-2">
              {steps.map((step, index) => {
                const active =
                  index === currentStep;

                const completed =
                  index < currentStep;

                return (
                  <div
                    key={step}
                    className={`flex items-center gap-3 rounded-xl px-3 py-3 ${
                      active
                        ? "bg-white shadow-sm ring-1 ring-slate-200"
                        : ""
                    }`}
                  >
                    <div
                      className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-semibold ${
                        active
                          ? "bg-slate-950 text-white"
                          : completed
                            ? "bg-green-100 text-green-700"
                            : "bg-slate-200 text-slate-600"
                      }`}
                    >
                      {completed
                        ? "✓"
                        : index + 1}
                    </div>

                    <span
                      className={
                        active
                          ? "font-medium text-slate-950"
                          : "text-sm text-slate-500"
                      }
                    >
                      {step}
                    </span>
                  </div>
                );
              })}
            </div>
          </aside>

          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm sm:p-8 lg:p-10">
            {currentStep === 0 && (
              <ProfileStepContent
                profileData={profileData}
                updateProfileField={
                  updateProfileField
                }
                handleSubmit={
                  handleProfileSubmit
                }
                isSaving={isSaving}
                error={error}
              />
            )}

            {currentStep === 1 && (
              <EducationStepContent
                educations={educations}
                educationData={
                  educationData
                }
                updateEducationField={
                  updateEducationField
                }
                handleSubmit={
                  handleEducationSubmit
                }
                isSaving={isSaving}
                error={error}
                onBack={() => {
                  setError("");
                  setCurrentStep(0);
                }}
                onContinue={() => {
                  setError("");
                  setCurrentStep(2);
                }}
              />
            )}

            {currentStep === 2 &&
              accessToken && (
                <ExperienceStep
                  accessToken={accessToken}
                  experiences={experiences}
                  setExperiences={
                    setExperiences
                  }
                  onBack={() =>
                    setCurrentStep(1)
                  }
                  onContinue={() =>
                    setCurrentStep(3)
                  }
                />
              )}

            {currentStep === 3 &&
              accessToken && (
                <ProjectStep
                  accessToken={accessToken}
                  projects={projects}
                  setProjects={setProjects}
                  onBack={() =>
                    setCurrentStep(2)
                  }
                  onContinue={() =>
                    setCurrentStep(4)
                  }
                />
              )}

            {currentStep === 4 &&
              accessToken && (
                <CertificationStep
                  accessToken={accessToken}
                  certifications={
                    certifications
                  }
                  setCertifications={
                    setCertifications
                  }
                  onBack={() =>
                    setCurrentStep(3)
                  }
                  onContinue={() =>
                    setCurrentStep(5)
                  }
                />
              )}

            {currentStep === 5 &&
              accessToken && (
                <CareerGoalStep
                  accessToken={accessToken}
                  careerGoals={careerGoals}
                  setCareerGoals={
                    setCareerGoals
                  }
                  onBack={() =>
                    setCurrentStep(4)
                  }
                />
              )}
          </section>
        </div>
      </div>
    </main>
  );
}

function ProfileStepContent({
  profileData,
  updateProfileField,
  handleSubmit,
  isSaving,
  error,
}: {
  profileData: StudentProfileData;
  updateProfileField: (
    field: keyof StudentProfileData,
    value: string
  ) => void;
  handleSubmit: (
    event: FormEvent<HTMLFormElement>
  ) => Promise<void>;
  isSaving: boolean;
  error: string;
}) {
  return (
    <>
      <StepHeader
        step="Step 1 of 6"
        title="Tell us about yourself"
        description="Start with your basic professional profile."
      />

      <form
        onSubmit={handleSubmit}
        className="mt-8"
      >
        <div className="grid gap-6 md:grid-cols-2">
          <div className="md:col-span-2">
            <TextInput
              id="full-name"
              label="Full name"
              required
              value={profileData.full_name}
              onChange={(value) =>
                updateProfileField(
                  "full_name",
                  value
                )
              }
            />
          </div>

          <TextInput
            id="phone"
            label="Phone"
            value={profileData.phone ?? ""}
            onChange={(value) =>
              updateProfileField(
                "phone",
                value
              )
            }
          />

          <TextInput
            id="city"
            label="City"
            value={profileData.city ?? ""}
            onChange={(value) =>
              updateProfileField(
                "city",
                value
              )
            }
          />

          <TextInput
            id="state"
            label="State"
            value={profileData.state ?? ""}
            onChange={(value) =>
              updateProfileField(
                "state",
                value
              )
            }
          />

          <TextInput
            id="country"
            label="Country"
            value={
              profileData.country ?? ""
            }
            onChange={(value) =>
              updateProfileField(
                "country",
                value
              )
            }
          />

          <div className="md:col-span-2">
            <TextInput
              id="headline"
              label="Professional headline"
              value={
                profileData.headline ?? ""
              }
              onChange={(value) =>
                updateProfileField(
                  "headline",
                  value
                )
              }
            />
          </div>

          <div className="md:col-span-2">
            <label
              htmlFor="bio"
              className={labelClass}
            >
              About you
            </label>

            <textarea
              id="bio"
              rows={5}
              value={profileData.bio ?? ""}
              onChange={(event) =>
                updateProfileField(
                  "bio",
                  event.target.value
                )
              }
              className={inputClass}
            />
          </div>
        </div>

        <ErrorMessage message={error} />

        <div className="mt-8 flex justify-end border-t border-slate-200 pt-6">
          <button
            type="submit"
            disabled={isSaving}
            className={primaryButton}
          >
            {isSaving
              ? "Saving..."
              : "Save & continue"}
          </button>
        </div>
      </form>
    </>
  );
}

function EducationStepContent({
  educations,
  educationData,
  updateEducationField,
  handleSubmit,
  isSaving,
  error,
  onBack,
  onContinue,
}: {
  educations: Education[];
  educationData: EducationData;
  updateEducationField: (
    field: keyof EducationData,
    value: string | number | undefined
  ) => void;
  handleSubmit: (
    event: FormEvent<HTMLFormElement>
  ) => Promise<void>;
  isSaving: boolean;
  error: string;
  onBack: () => void;
  onContinue: () => void;
}) {
  return (
    <>
      <StepHeader
        step="Step 2 of 6"
        title="Education"
        description="Add your current or previous education. You can add more than one qualification."
      />

      {educations.length > 0 && (
        <div className="mt-8 space-y-3">
          <p className="text-sm font-semibold text-slate-700">
            Added education
          </p>

          {educations.map((education) => (
            <div
              key={education.id}
              className="rounded-xl border border-slate-200 bg-slate-50 p-4"
            >
              <p className="font-semibold text-slate-950">
                {education.degree}
              </p>

              <p className="mt-1 text-sm text-slate-600">
                {
                  education.institution_name
                }
              </p>

              {education.field_of_study && (
                <p className="mt-1 text-sm text-slate-500">
                  {
                    education.field_of_study
                  }
                </p>
              )}

              {(education.start_year ||
                education.end_year) && (
                <p className="mt-2 text-xs text-slate-500">
                  {education.start_year ??
                    "—"}{" "}
                  –{" "}
                  {education.end_year ??
                    "Present"}
                </p>
              )}
            </div>
          ))}
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        className="mt-8"
      >
        <div className="grid gap-6 md:grid-cols-2">
          <div className="md:col-span-2">
            <TextInput
              id="institution"
              label="Institution name"
              required
              value={
                educationData.institution_name
              }
              placeholder="University or college"
              onChange={(value) =>
                updateEducationField(
                  "institution_name",
                  value
                )
              }
            />
          </div>

          <TextInput
            id="degree"
            label="Degree"
            required
            value={educationData.degree}
            placeholder="B.Tech"
            onChange={(value) =>
              updateEducationField(
                "degree",
                value
              )
            }
          />

          <TextInput
            id="field"
            label="Field of study"
            value={
              educationData.field_of_study ??
              ""
            }
            placeholder="Artificial Intelligence"
            onChange={(value) =>
              updateEducationField(
                "field_of_study",
                value
              )
            }
          />

          <NumberInput
            id="start-year"
            label="Start year"
            value={
              educationData.start_year
            }
            placeholder="2023"
            onChange={(value) =>
              updateEducationField(
                "start_year",
                value
              )
            }
          />

          <NumberInput
            id="end-year"
            label="End year"
            value={educationData.end_year}
            placeholder="2027"
            onChange={(value) =>
              updateEducationField(
                "end_year",
                value
              )
            }
          />

          <div className="md:col-span-2">
            <TextInput
              id="grade"
              label="Grade / CGPA"
              value={
                educationData.grade ?? ""
              }
              placeholder="8.5 CGPA"
              onChange={(value) =>
                updateEducationField(
                  "grade",
                  value
                )
              }
            />
          </div>
        </div>

        <ErrorMessage message={error} />

        <div className="mt-8 flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 pt-6">
          <button
            type="button"
            onClick={onBack}
            className={secondaryButton}
          >
            Back
          </button>

          <div className="flex gap-3">
            <button
              type="submit"
              disabled={isSaving}
              className={secondaryButton}
            >
              {isSaving
                ? "Saving..."
                : "Add education"}
            </button>

            <button
              type="button"
              disabled={
                educations.length === 0
              }
              onClick={onContinue}
              className={`${primaryButton} disabled:cursor-not-allowed disabled:opacity-40`}
            >
              Continue
            </button>
          </div>
        </div>
      </form>
    </>
  );
}

function StepHeader({
  step,
  title,
  description,
}: {
  step: string;
  title: string;
  description: string;
}) {
  return (
    <div className="border-b border-slate-200 pb-6">
      <p className="text-sm font-medium text-blue-600">
        {step}
      </p>

      <h2 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">
        {title}
      </h2>

      <p className="mt-3 max-w-2xl text-slate-600">
        {description}
      </p>
    </div>
  );
}

function TextInput({
  id,
  label,
  value,
  onChange,
  placeholder,
  required = false,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  required?: boolean;
}) {
  return (
    <div>
      <label
        htmlFor={id}
        className={labelClass}
      >
        {label}
      </label>

      <input
        id={id}
        required={required}
        value={value}
        placeholder={placeholder}
        onChange={(event) =>
          onChange(event.target.value)
        }
        className={inputClass}
      />
    </div>
  );
}

function NumberInput({
  id,
  label,
  value,
  placeholder,
  onChange,
}: {
  id: string;
  label: string;
  value?: number | null;
  placeholder?: string;
  onChange: (
    value: number | undefined
  ) => void;
}) {
  return (
    <div>
      <label
        htmlFor={id}
        className={labelClass}
      >
        {label}
      </label>

      <input
        id={id}
        type="number"
        min="1900"
        max="2100"
        value={value ?? ""}
        placeholder={placeholder}
        onChange={(event) =>
          onChange(
            event.target.value
              ? Number(event.target.value)
              : undefined
          )
        }
        className={inputClass}
      />
    </div>
  );
}

function ErrorMessage({
  message,
}: {
  message: string;
}) {
  if (!message) {
    return null;
  }

  return (
    <div
      role="alert"
      className="mt-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
    >
      {message}
    </div>
  );
}

const labelClass =
  "mb-2 block text-sm font-medium text-slate-700";

const inputClass =
  "w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-blue-600 focus:ring-4 focus:ring-blue-100";

const primaryButton =
  "rounded-xl bg-slate-950 px-6 py-3 font-medium text-white hover:bg-slate-800 disabled:opacity-60";

const secondaryButton =
  "rounded-xl border border-slate-300 px-5 py-3 font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-60";