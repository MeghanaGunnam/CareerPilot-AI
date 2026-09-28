"use client";

import { FormEvent, useState } from "react";

import {
  createExperience,
  deleteExperience,
  type Experience,
  type ExperienceData,
} from "@/lib/api/students";
import { ApiError } from "@/lib/api/client";

interface ExperienceStepProps {
  accessToken: string;
  experiences: Experience[];
  setExperiences: (
    value:
      | Experience[]
      | ((current: Experience[]) => Experience[])
  ) => void;
  onBack: () => void;
  onContinue: () => void;
}

const emptyExperience: ExperienceData = {
  company_name: "",
  job_title: "",
  employment_type: "",
  location: "",
  start_date: "",
  end_date: null,
  is_current: false,
  description: "",
};

export default function ExperienceStep({
  accessToken,
  experiences,
  setExperiences,
  onBack,
  onContinue,
}: ExperienceStepProps) {
  const [formData, setFormData] =
    useState<ExperienceData>(emptyExperience);

  const [isSaving, setIsSaving] =
    useState(false);

  const [error, setError] = useState("");

  function updateField(
    field: keyof ExperienceData,
    value: string | boolean | null
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
      const savedExperience =
        await createExperience(
          accessToken,
          formData
        );

      setExperiences((current) => [
        ...current,
        savedExperience,
      ]);

      setFormData(emptyExperience);
    } catch (error) {
      if (error instanceof ApiError) {
        setError(error.message);
      } else {
        setError(
          "Unable to save your experience."
        );
      }
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDelete(id: string) {
    setError("");

    try {
      await deleteExperience(
        accessToken,
        id
      );

      setExperiences((current) =>
        current.filter(
          (experience) =>
            experience.id !== id
        )
      );
    } catch (error) {
      if (error instanceof ApiError) {
        setError(error.message);
      } else {
        setError(
          "Unable to delete experience."
        );
      }
    }
  }

  return (
    <>
      <StepHeader
        step="Step 3 of 6"
        title="Professional experience"
        description="Add internships, part-time work, freelance work, or professional experience. Freshers can continue without adding an experience."
      />

      {experiences.length > 0 && (
        <div className="mt-8 space-y-3">
          <p className="text-sm font-semibold text-slate-700">
            Added experience
          </p>

          {experiences.map((experience) => (
            <div
              key={experience.id}
              className="flex items-start justify-between gap-4 rounded-xl border border-slate-200 bg-slate-50 p-4"
            >
              <div>
                <p className="font-semibold text-slate-950">
                  {experience.job_title}
                </p>

                <p className="mt-1 text-sm text-slate-600">
                  {experience.company_name}
                </p>

                {experience.employment_type && (
                  <p className="mt-1 text-sm text-slate-500">
                    {
                      experience.employment_type
                    }
                  </p>
                )}

                <p className="mt-2 text-xs text-slate-500">
                  {formatDate(
                    experience.start_date
                  )}{" "}
                  –{" "}
                  {experience.is_current
                    ? "Present"
                    : experience.end_date
                      ? formatDate(
                          experience.end_date
                        )
                      : "—"}
                </p>
              </div>

              <button
                type="button"
                onClick={() =>
                  handleDelete(experience.id)
                }
                className="text-sm font-medium text-red-600 hover:text-red-700"
              >
                Remove
              </button>
            </div>
          ))}
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        className="mt-8"
      >
        <div className="grid gap-6 md:grid-cols-2">
          <TextInput
            id="company-name"
            label="Company / organization"
            value={formData.company_name}
            required
            onChange={(value) =>
              updateField(
                "company_name",
                value
              )
            }
          />

          <TextInput
            id="job-title"
            label="Role / job title"
            value={formData.job_title}
            required
            onChange={(value) =>
              updateField(
                "job_title",
                value
              )
            }
          />

          <TextInput
            id="employment-type"
            label="Employment type"
            value={
              formData.employment_type ?? ""
            }
            placeholder="Internship, Full-time..."
            onChange={(value) =>
              updateField(
                "employment_type",
                value
              )
            }
          />

          <TextInput
            id="experience-location"
            label="Location"
            value={formData.location ?? ""}
            onChange={(value) =>
              updateField("location", value)
            }
          />

          <DateInput
            id="experience-start"
            label="Start date"
            value={formData.start_date}
            required
            onChange={(value) =>
              updateField(
                "start_date",
                value
              )
            }
          />

          <DateInput
            id="experience-end"
            label="End date"
            value={formData.end_date ?? ""}
            disabled={
              formData.is_current ?? false
            }
            onChange={(value) =>
              updateField(
                "end_date",
                value || null
              )
            }
          />

          <label className="flex items-center gap-3 md:col-span-2">
            <input
              type="checkbox"
              checked={
                formData.is_current ?? false
              }
              onChange={(event) =>
                setFormData((current) => ({
                  ...current,
                  is_current:
                    event.target.checked,
                  end_date:
                    event.target.checked
                      ? null
                      : current.end_date,
                }))
              }
              className="h-4 w-4"
            />

            <span className="text-sm font-medium text-slate-700">
              I currently work here
            </span>
          </label>

          <div className="md:col-span-2">
            <label
              htmlFor="experience-description"
              className="mb-2 block text-sm font-medium text-slate-700"
            >
              Description
            </label>

            <textarea
              id="experience-description"
              rows={4}
              value={
                formData.description ?? ""
              }
              onChange={(event) =>
                updateField(
                  "description",
                  event.target.value
                )
              }
              placeholder="Describe what you worked on and your responsibilities."
              className={inputClass}
            />
          </div>
        </div>

        {error && (
          <ErrorMessage message={error} />
        )}

        <div className="mt-8 flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 pt-6">
          <button
            type="button"
            onClick={onBack}
            className={secondaryButton}
          >
            Back
          </button>

          <div className="flex flex-wrap gap-3">
            <button
              type="submit"
              disabled={isSaving}
              className={secondaryButton}
            >
              {isSaving
                ? "Saving..."
                : "Add experience"}
            </button>

            <button
              type="button"
              onClick={onContinue}
              className={primaryButton}
            >
              {experiences.length === 0
                ? "I have no experience — Continue"
                : "Continue"}
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

function DateInput({
  id,
  label,
  value,
  onChange,
  required = false,
  disabled = false,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
  disabled?: boolean;
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
        type="date"
        required={required}
        disabled={disabled}
        value={value}
        onChange={(event) =>
          onChange(event.target.value)
        }
        className={`${inputClass} disabled:bg-slate-100`}
      />
    </div>
  );
}

function ErrorMessage({
  message,
}: {
  message: string;
}) {
  return (
    <div
      role="alert"
      className="mt-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
    >
      {message}
    </div>
  );
}

function formatDate(value: string) {
  return new Date(value).toLocaleDateString(
    undefined,
    {
      year: "numeric",
      month: "short",
    }
  );
}

const inputClass =
  "w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-blue-600 focus:ring-4 focus:ring-blue-100";

const primaryButton =
  "rounded-xl bg-slate-950 px-6 py-3 font-medium text-white hover:bg-slate-800";

const secondaryButton =
  "rounded-xl border border-slate-300 px-5 py-3 font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-60";