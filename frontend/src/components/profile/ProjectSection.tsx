"use client";

import { useState } from "react";

import {
  createProject,
  updateProject,
  deleteProject,
  type Project,
  type ProjectData,
} from "@/lib/api/students";

interface Props {
  accessToken: string;
  projects: Project[];
  onChange: (items: Project[]) => void;
  onMessage: (message: string) => void;
  onError: (message: string) => void;
}

const EMPTY_FORM: ProjectData = {
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

export default function ProjectSection({
  accessToken,
  projects,
  onChange,
  onMessage,
  onError,
}: Props) {
  const [form, setForm] =
    useState<ProjectData>(EMPTY_FORM);

  const [editingId, setEditingId] =
    useState<string | null>(null);

  const [isSaving, setIsSaving] =
    useState(false);

  const [deletingId, setDeletingId] =
    useState<string | null>(null);

  function reset() {
    setForm(EMPTY_FORM);
    setEditingId(null);
  }

  function edit(item: Project) {
    setEditingId(item.id);

    setForm({
      title: item.title,
      description: item.description ?? "",
      role: item.role ?? "",
      technologies: item.technologies ?? "",
      project_url: item.project_url ?? "",
      repository_url: item.repository_url ?? "",
      start_date: item.start_date,
      end_date: item.end_date,
      is_ongoing: item.is_ongoing,
    });
  }

  async function save() {
    if (!form.title.trim()) {
      onError("Project title is required.");
      return;
    }

    try {
      setIsSaving(true);

      const payload: ProjectData = {
        ...form,
        title: form.title.trim(),
        end_date: form.is_ongoing
          ? null
          : form.end_date,
      };

      if (editingId) {
        const updated = await updateProject(
          accessToken,
          editingId,
          payload,
        );

        onChange(
          projects.map((item) =>
            item.id === editingId
              ? updated
              : item,
          ),
        );

        onMessage(
          "Project updated successfully.",
        );
      } else {
        const created = await createProject(
          accessToken,
          payload,
        );

        onChange([...projects, created]);

        onMessage(
          "Project added successfully.",
        );
      }

      reset();
    } catch (error) {
      onError(
        error instanceof Error
          ? error.message
          : "Unable to save project.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  async function remove(id: string) {
    if (!window.confirm("Delete this project?")) {
      return;
    }

    try {
      setDeletingId(id);

      await deleteProject(accessToken, id);

      onChange(
        projects.filter(
          (item) => item.id !== id,
        ),
      );

      if (editingId === id) {
        reset();
      }

      onMessage(
        "Project deleted successfully.",
      );
    } catch (error) {
      onError(
        error instanceof Error
          ? error.message
          : "Unable to delete project.",
      );
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <section className="mt-8 rounded-3xl border border-slate-200 bg-white p-7 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wider text-blue-600">
            Practical Work
          </p>

          <h2 className="mt-2 text-2xl font-bold text-slate-950">
            Projects
          </h2>
        </div>

        {editingId && (
          <button
            type="button"
            onClick={reset}
            className="text-sm font-semibold text-slate-600"
          >
            Cancel
          </button>
        )}
      </div>

      {projects.length > 0 && (
        <div className="mt-6 space-y-3">
          {projects.map((item) => (
            <article
              key={item.id}
              className="rounded-2xl border border-slate-200 p-5"
            >
              <div className="flex flex-col justify-between gap-4 sm:flex-row">
                <div>
                  <h3 className="font-semibold text-slate-950">
                    {item.title}
                  </h3>

                  {item.role && (
                    <p className="mt-1 text-sm text-slate-600">
                      Role: {item.role}
                    </p>
                  )}

                  {item.technologies && (
                    <p className="mt-1 text-sm text-slate-500">
                      Technologies:{" "}
                      {item.technologies}
                    </p>
                  )}

                  {item.description && (
                    <p className="mt-3 whitespace-pre-line text-sm leading-6 text-slate-600">
                      {item.description}
                    </p>
                  )}

                  <div className="mt-3 flex flex-wrap gap-3 text-sm">
                    {item.project_url && (
                      <a
                        href={item.project_url}
                        target="_blank"
                        rel="noreferrer"
                        className="font-medium text-blue-600"
                      >
                        Project
                      </a>
                    )}

                    {item.repository_url && (
                      <a
                        href={item.repository_url}
                        target="_blank"
                        rel="noreferrer"
                        className="font-medium text-blue-600"
                      >
                        Repository
                      </a>
                    )}
                  </div>
                </div>

                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => edit(item)}
                    className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium"
                  >
                    Edit
                  </button>

                  <button
                    type="button"
                    disabled={deletingId === item.id}
                    onClick={() => remove(item.id)}
                    className="rounded-lg border border-red-200 px-3 py-2 text-sm font-medium text-red-600 disabled:opacity-50"
                  >
                    {deletingId === item.id
                      ? "Deleting..."
                      : "Delete"}
                  </button>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        <Input
          label="Project title"
          value={form.title}
          onChange={(value) =>
            setForm((old) => ({
              ...old,
              title: value,
            }))
          }
        />

        <Input
          label="Your role"
          value={form.role ?? ""}
          onChange={(value) =>
            setForm((old) => ({
              ...old,
              role: value,
            }))
          }
        />

        <Input
          label="Technologies"
          value={form.technologies ?? ""}
          onChange={(value) =>
            setForm((old) => ({
              ...old,
              technologies: value,
            }))
          }
        />

        <Input
          label="Project URL"
          value={form.project_url ?? ""}
          onChange={(value) =>
            setForm((old) => ({
              ...old,
              project_url: value,
            }))
          }
        />

        <Input
          label="Repository URL"
          value={form.repository_url ?? ""}
          onChange={(value) =>
            setForm((old) => ({
              ...old,
              repository_url: value,
            }))
          }
        />

        <DateInput
          label="Start date"
          value={form.start_date ?? ""}
          onChange={(value) =>
            setForm((old) => ({
              ...old,
              start_date: value || null,
            }))
          }
        />

        {!form.is_ongoing && (
          <DateInput
            label="End date"
            value={form.end_date ?? ""}
            onChange={(value) =>
              setForm((old) => ({
                ...old,
                end_date: value || null,
              }))
            }
          />
        )}
      </div>

      <label className="mt-5 flex items-center gap-3 text-sm text-slate-700">
        <input
          type="checkbox"
          checked={form.is_ongoing ?? false}
          onChange={(event) =>
            setForm((old) => ({
              ...old,
              is_ongoing: event.target.checked,
              end_date: event.target.checked
                ? null
                : old.end_date,
            }))
          }
        />
        This project is ongoing
      </label>

      <div className="mt-5">
        <label className="text-sm font-medium text-slate-700">
          Description
        </label>

        <textarea
          rows={4}
          value={form.description ?? ""}
          onChange={(event) =>
            setForm((old) => ({
              ...old,
              description: event.target.value,
            }))
          }
          className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
        />
      </div>

      <div className="mt-5 flex justify-end">
        <button
          type="button"
          disabled={isSaving}
          onClick={save}
          className="rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {isSaving
            ? "Saving..."
            : editingId
              ? "Update Project"
              : "Add Project"}
        </button>
      </div>
    </section>
  );
}

function Input({
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
        value={value}
        onChange={(event) =>
          onChange(event.target.value)
        }
        className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
      />
    </div>
  );
}

function DateInput({
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
        type="date"
        value={value}
        onChange={(event) =>
          onChange(event.target.value)
        }
        className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
      />
    </div>
  );
}