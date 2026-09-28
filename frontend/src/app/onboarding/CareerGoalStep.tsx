"use client";

import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

import { ApiError } from "@/lib/api/client";
import {
  createCareerGoal,
  type CareerGoal,
  type CareerGoalData,
} from "@/lib/api/students";

interface CareerGoalStepProps {
  accessToken: string;
  careerGoals: CareerGoal[];
  setCareerGoals: (
    value:
      | CareerGoal[]
      | ((
          current: CareerGoal[]
        ) => CareerGoal[])
  ) => void;
  onBack: () => void;
}

const emptyCareerGoal: CareerGoalData = {
  target_role: "",
  target_industry: "",
  target_location: "",
  employment_type: "",
  target_timeline_months: 12,
  priority: 5,
  is_active: true,
  notes: "",
};

export default function CareerGoalStep({
  accessToken,
  careerGoals,
  setCareerGoals,
  onBack,
}: CareerGoalStepProps) {
  const router = useRouter();

  const [formData, setFormData] =
    useState<CareerGoalData>(
      emptyCareerGoal
    );

  const [isSaving, setIsSaving] =
    useState(false);

  const [error, setError] = useState("");

  function updateField(
    field: keyof CareerGoalData,
    value: string | number | boolean
  ) {
    setFormData((current) => ({
      ...current,
      [field]: value,
    }));
  }

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>
  ) {
    event.preventDefault();

    setError("");
    setIsSaving(true);

    try {
      const savedGoal =
        await createCareerGoal(
          accessToken,
          formData
        );

      setCareerGoals((current) => [
        ...current,
        savedGoal,
      ]);

      router.replace("/dashboard");
    } catch (error) {
      if (error instanceof ApiError) {
        setError(error.message);
      } else {
        setError(
          "Unable to save your career goal."
        );
      }
    } finally {
      setIsSaving(false);
    }
  }

  if (careerGoals.length > 0) {
    return (
      <>
        <Header />

        <div className="mt-8 rounded-2xl border border-green-200 bg-green-50 p-6">
          <p className="text-sm font-semibold text-green-700">
            Career goal configured
          </p>

          <h3 className="mt-2 text-xl font-semibold text-slate-950">
            {careerGoals[0].target_role}
          </h3>

          {careerGoals[0].target_industry && (
            <p className="mt-1 text-sm text-slate-600">
              {
                careerGoals[0]
                  .target_industry
              }
            </p>
          )}

          <p className="mt-4 text-sm text-slate-600">
            Your onboarding foundation is
            complete. CareerPilot can now begin
            building your career intelligence
            profile.
          </p>
        </div>

        <div className="mt-8 flex items-center justify-between border-t border-slate-200 pt-6">
          <button
            type="button"
            onClick={onBack}
            className={secondaryButton}
          >
            Back
          </button>

          <button
            type="button"
            onClick={() =>
              router.replace("/dashboard")
            }
            className={primaryButton}
          >
            Go to dashboard
          </button>
        </div>
      </>
    );
  }

  return (
    <>
      <Header />

      <form
        onSubmit={handleSubmit}
        className="mt-8"
      >
        <div className="grid gap-6 md:grid-cols-2">
          <div className="md:col-span-2">
            <Input
              id="target-role"
              label="Target role"
              required
              value={formData.target_role}
              placeholder="Machine Learning Engineer"
              onChange={(value) =>
                updateField(
                  "target_role",
                  value
                )
              }
            />
          </div>

          <Input
            id="target-industry"
            label="Target industry"
            value={
              formData.target_industry ?? ""
            }
            placeholder="Technology"
            onChange={(value) =>
              updateField(
                "target_industry",
                value
              )
            }
          />

          <Input
            id="target-location"
            label="Preferred location"
            value={
              formData.target_location ?? ""
            }
            placeholder="Hyderabad / Remote"
            onChange={(value) =>
              updateField(
                "target_location",
                value
              )
            }
          />

          <div>
            <label
              htmlFor="employment-type"
              className="mb-2 block text-sm font-medium text-slate-700"
            >
              Employment type
            </label>

            <select
              id="employment-type"
              value={
                formData.employment_type ?? ""
              }
              onChange={(event) =>
                updateField(
                  "employment_type",
                  event.target.value
                )
              }
              className={inputClass}
            >
              <option value="">
                Select preference
              </option>
              <option value="Full-time">
                Full-time
              </option>
              <option value="Internship">
                Internship
              </option>
              <option value="Part-time">
                Part-time
              </option>
              <option value="Contract">
                Contract
              </option>
              <option value="Remote">
                Remote
              </option>
            </select>
          </div>

          <div>
            <label
              htmlFor="timeline"
              className="mb-2 block text-sm font-medium text-slate-700"
            >
              Target timeline
            </label>

            <select
              id="timeline"
              value={
                formData.target_timeline_months ??
                12
              }
              onChange={(event) =>
                updateField(
                  "target_timeline_months",
                  Number(event.target.value)
                )
              }
              className={inputClass}
            >
              <option value={3}>
                Within 3 months
              </option>
              <option value={6}>
                Within 6 months
              </option>
              <option value={12}>
                Within 1 year
              </option>
              <option value={24}>
                Within 2 years
              </option>
              <option value={36}>
                Within 3 years
              </option>
            </select>
          </div>

          <div className="md:col-span-2">
            <label
              htmlFor="priority"
              className="mb-2 block text-sm font-medium text-slate-700"
            >
              Goal priority:{" "}
              {formData.priority ?? 5}/10
            </label>

            <input
              id="priority"
              type="range"
              min="1"
              max="10"
              value={formData.priority ?? 5}
              onChange={(event) =>
                updateField(
                  "priority",
                  Number(event.target.value)
                )
              }
              className="w-full"
            />
          </div>

          <div className="md:col-span-2">
            <label
              htmlFor="goal-notes"
              className="mb-2 block text-sm font-medium text-slate-700"
            >
              Additional notes
            </label>

            <textarea
              id="goal-notes"
              rows={5}
              value={formData.notes ?? ""}
              onChange={(event) =>
                updateField(
                  "notes",
                  event.target.value
                )
              }
              placeholder="Tell CareerPilot anything important about your career goal."
              className={inputClass}
            />
          </div>
        </div>

        {error && (
          <div
            role="alert"
            className="mt-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
          >
            {error}
          </div>
        )}

        <div className="mt-8 flex items-center justify-between border-t border-slate-200 pt-6">
          <button
            type="button"
            onClick={onBack}
            className={secondaryButton}
          >
            Back
          </button>

          <button
            type="submit"
            disabled={isSaving}
            className={`${primaryButton} disabled:opacity-60`}
          >
            {isSaving
              ? "Completing onboarding..."
              : "Complete onboarding"}
          </button>
        </div>
      </form>
    </>
  );
}

function Header() {
  return (
    <div className="border-b border-slate-200 pb-6">
      <p className="text-sm font-medium text-blue-600">
        Step 6 of 6
      </p>

      <h2 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">
        Career goal
      </h2>

      <p className="mt-3 max-w-2xl text-slate-600">
        Tell CareerPilot where you want to go.
        Your goal will later be evaluated
        against your Career Twin, skills and
        career requirements.
      </p>
    </div>
  );
}

function Input({
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
        className="mb-2 block text-sm font-medium text-slate-700"
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

const inputClass =
  "w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-blue-600 focus:ring-4 focus:ring-blue-100";

const primaryButton =
  "rounded-xl bg-slate-950 px-6 py-3 font-medium text-white hover:bg-slate-800";

const secondaryButton =
  "rounded-xl border border-slate-300 px-5 py-3 font-medium text-slate-700 hover:bg-slate-50";