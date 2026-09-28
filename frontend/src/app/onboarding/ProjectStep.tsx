"use client";

import { FormEvent, useState } from "react";

import {
  createProject,
  deleteProject,
  type Project,
  type ProjectData,
} from "@/lib/api/students";
import { ApiError } from "@/lib/api/client";

interface ProjectStepProps {
  accessToken: string;
  projects: Project[];
  setProjects: (
    value:
      | Project[]
      | ((current: Project[]) => Project[])
  ) => void;
  onBack: () => void;
  onContinue: () => void;
}

const emptyProject: ProjectData = {
  title: "",
  description: "",
  role: "",
  technologies: "",
  project_url: "",
  repository_url: "",
  start_date: null,
  end_date: null,
  is_ongoing: false,
};

export default function ProjectStep({
  accessToken,
  projects,
  setProjects,
  onBack,
  onContinue,
}: ProjectStepProps) {
  const [formData, setFormData] =
    useState<ProjectData>(emptyProject);

  const [isSaving, setIsSaving] =
    useState(false);

  const [error, setError] = useState("");

  function updateField(
    field: keyof ProjectData,
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
      const savedProject =
        await createProject(
          accessToken,
          formData
        );

      setProjects((current) => [
        ...current,
        savedProject,
      ]);

      setFormData(emptyProject);
    } catch (error) {
      if (error instanceof ApiError) {
        setError(error.message);
      } else {
        setError(
          "Unable to save your project."
        );
      }
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDelete(id: string) {
    setError("");

    try {
      await deleteProject(
        accessToken,
        id
      );

      setProjects((current) =>
        current.filter(
          (project) => project.id !== id
        )
      );
    } catch (error) {
      if (error instanceof ApiError) {
        setError(error.message);
      } else {
        setError(
          "Unable to delete project."
        );
      }
    }
  }

  return (
    <>
      <div className="border-b border-slate-200 pb-6">
        <p className="text-sm font-medium text-blue-600">
          Step 4 of 6
        </p>

        <h2 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">
          Projects
        </h2>

        <p className="mt-3 max-w-2xl text-slate-600">
          Add projects that demonstrate your
          skills. These will later become
          important evidence in your Career Twin.
        </p>
      </div>

      {projects.length > 0 && (
        <div className="mt-8 space-y-3">
          <p className="text-sm font-semibold text-slate-700">
            Added projects
          </p>

          {projects.map((project) => (
            <div
              key={project.id}
              className="flex items-start justify-between gap-4 rounded-xl border border-slate-200 bg-slate-50 p-4"
            >
              <div>
                <p className="font-semibold text-slate-950">
                  {project.title}
                </p>

                {project.role && (
                  <p className="mt-1 text-sm text-slate-600">
                    {project.role}
                  </p>
                )}

                {project.technologies && (
                  <p className="mt-2 text-sm text-slate-500">
                    {project.technologies}
                  </p>
                )}
              </div>

              <button
                type="button"
                onClick={() =>
                  handleDelete(project.id)
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
          <div className="md:col-span-2">
            <Input
              id="project-title"
              label="Project title"
              required
              value={formData.title}
              onChange={(value) =>
                updateField("title", value)
              }
            />
          </div>

          <Input
            id="project-role"
            label="Your role"
            value={formData.role ?? ""}
            placeholder="Developer"
            onChange={(value) =>
              updateField("role", value)
            }
          />

          <Input
            id="project-technologies"
            label="Technologies"
            value={
              formData.technologies ?? ""
            }
            placeholder="Python, FastAPI, PostgreSQL"
            onChange={(value) =>
              updateField(
                "technologies",
                value
              )
            }
          />

          <Input
            id="project-url"
            label="Project URL"
            type="url"
            value={
              formData.project_url ?? ""
            }
            onChange={(value) =>
              updateField(
                "project_url",
                value
              )
            }
          />

          <Input
            id="repository-url"
            label="Repository URL"
            type="url"
            value={
              formData.repository_url ?? ""
            }
            onChange={(value) =>
              updateField(
                "repository_url",
                value
              )
            }
          />

          <Input
            id="project-start"
            label="Start date"
            type="date"
            value={
              formData.start_date ?? ""
            }
            onChange={(value) =>
              updateField(
                "start_date",
                value || null
              )
            }
          />

          <Input
            id="project-end"
            label="End date"
            type="date"
            disabled={
              formData.is_ongoing ?? false
            }
            value={formData.end_date ?? ""}
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
                formData.is_ongoing ?? false
              }
              onChange={(event) =>
                setFormData((current) => ({
                  ...current,
                  is_ongoing:
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
              This project is ongoing
            </span>
          </label>

          <div className="md:col-span-2">
            <label
              htmlFor="project-description"
              className="mb-2 block text-sm font-medium text-slate-700"
            >
              Description
            </label>

            <textarea
              id="project-description"
              rows={5}
              value={
                formData.description ?? ""
              }
              onChange={(event) =>
                updateField(
                  "description",
                  event.target.value
                )
              }
              placeholder="Explain what you built, how it works, and its purpose."
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
                : "Add project"}
            </button>

            <button
              type="button"
              disabled={projects.length === 0}
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

function Input({
  id,
  label,
  value,
  onChange,
  type = "text",
  placeholder,
  required = false,
  disabled = false,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
  placeholder?: string;
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
        type={type}
        value={value}
        required={required}
        disabled={disabled}
        placeholder={placeholder}
        onChange={(event) =>
          onChange(event.target.value)
        }
        className={`${inputClass} disabled:bg-slate-100`}
      />
    </div>
  );
}

const inputClass =
  "w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:border-blue-600 focus:ring-4 focus:ring-blue-100";

const primaryButton =
  "rounded-xl bg-slate-950 px-6 py-3 font-medium text-white hover:bg-slate-800";

const secondaryButton =
  "rounded-xl border border-slate-300 px-5 py-3 font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-60";