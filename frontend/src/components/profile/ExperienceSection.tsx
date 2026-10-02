"use client";

import { useState } from "react";

import {
  createExperience,
  updateExperience,
  deleteExperience,
  type Experience,
  type ExperienceData,
} from "@/lib/api/students";

interface Props {
  accessToken: string;
  experiences: Experience[];
  onChange: (items: Experience[]) => void;
  onMessage: (message: string) => void;
  onError: (message: string) => void;
}

const EMPTY_FORM: ExperienceData = {
  company_name: "",
  job_title: "",
  employment_type: "",
  location: "",
  start_date: "",
  end_date: null,
  is_current: false,
  description: "",
};

export default function ExperienceSection({
  accessToken,
  experiences,
  onChange,
  onMessage,
  onError,
}: Props) {
  const [form, setForm] =
    useState<ExperienceData>(EMPTY_FORM);

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

  function edit(item: Experience) {
    setEditingId(item.id);

    setForm({
      company_name: item.company_name,
      job_title: item.job_title,
      employment_type: item.employment_type ?? "",
      location: item.location ?? "",
      start_date: item.start_date,
      end_date: item.end_date,
      is_current: item.is_current,
      description: item.description ?? "",
    });
  }

  async function save() {
    if (
      !form.company_name.trim() ||
      !form.job_title.trim() ||
      !form.start_date
    ) {
      onError(
        "Company, job title and start date are required.",
      );
      return;
    }

    try {
      setIsSaving(true);

      const payload: ExperienceData = {
        ...form,
        company_name: form.company_name.trim(),
        job_title: form.job_title.trim(),
        end_date: form.is_current
          ? null
          : form.end_date,
      };

      if (editingId) {
        const updated = await updateExperience(
          accessToken,
          editingId,
          payload,
        );

        onChange(
          experiences.map((item) =>
            item.id === editingId
              ? updated
              : item,
          ),
        );

        onMessage(
          "Experience updated successfully.",
        );
      } else {
        const created = await createExperience(
          accessToken,
          payload,
        );

        onChange([...experiences, created]);

        onMessage(
          "Experience added successfully.",
        );
      }

      reset();
    } catch (error) {
      onError(
        error instanceof Error
          ? error.message
          : "Unable to save experience.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  async function remove(id: string) {
    if (!window.confirm("Delete this experience?")) {
      return;
    }

    try {
      setDeletingId(id);

      await deleteExperience(accessToken, id);

      onChange(
        experiences.filter(
          (item) => item.id !== id,
        ),
      );

      if (editingId === id) {
        reset();
      }

      onMessage(
        "Experience deleted successfully.",
      );
    } catch (error) {
      onError(
        error instanceof Error
          ? error.message
          : "Unable to delete experience.",
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
            Professional Background
          </p>

          <h2 className="mt-2 text-2xl font-bold text-slate-950">
            Experience
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

      {experiences.length > 0 && (
        <div className="mt-6 space-y-3">
          {experiences.map((item) => (
            <article
              key={item.id}
              className="rounded-2xl border border-slate-200 p-5"
            >
              <div className="flex flex-col justify-between gap-4 sm:flex-row">
                <div>
                  <h3 className="font-semibold text-slate-950">
                    {item.job_title}
                  </h3>

                  <p className="mt-1 text-sm text-slate-600">
                    {item.company_name}
                  </p>

                  <p className="mt-1 text-sm text-slate-500">
                    {item.start_date} –{" "}
                    {item.is_current
                      ? "Present"
                      : item.end_date ?? "Unknown"}
                  </p>

                  {item.employment_type && (
                    <p className="mt-1 text-sm text-slate-500">
                      {item.employment_type}
                    </p>
                  )}

                  {item.location && (
                    <p className="mt-1 text-sm text-slate-500">
                      {item.location}
                    </p>
                  )}

                  {item.description && (
                    <p className="mt-3 whitespace-pre-line text-sm leading-6 text-slate-600">
                      {item.description}
                    </p>
                  )}
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
          label="Company"
          value={form.company_name}
          onChange={(value) =>
            setForm((old) => ({
              ...old,
              company_name: value,
            }))
          }
        />

        <Input
          label="Job title"
          value={form.job_title}
          onChange={(value) =>
            setForm((old) => ({
              ...old,
              job_title: value,
            }))
          }
        />

        <Input
          label="Employment type"
          value={form.employment_type ?? ""}
          onChange={(value) =>
            setForm((old) => ({
              ...old,
              employment_type: value,
            }))
          }
        />

        <Input
          label="Location"
          value={form.location ?? ""}
          onChange={(value) =>
            setForm((old) => ({
              ...old,
              location: value,
            }))
          }
        />

        <DateInput
          label="Start date"
          value={form.start_date}
          onChange={(value) =>
            setForm((old) => ({
              ...old,
              start_date: value,
            }))
          }
        />

        {!form.is_current && (
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
          checked={form.is_current ?? false}
          onChange={(event) =>
            setForm((old) => ({
              ...old,
              is_current: event.target.checked,
              end_date: event.target.checked
                ? null
                : old.end_date,
            }))
          }
        />

        I currently work here
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
              ? "Update Experience"
              : "Add Experience"}
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