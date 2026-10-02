"use client";

import { useState } from "react";

import {
  createEducation,
  updateEducation,
  deleteEducation,
  type Education,
  type EducationData,
} from "@/lib/api/students";

interface EducationSectionProps {
  accessToken: string;
  educations: Education[];
  onChange: (educations: Education[]) => void;
  onMessage: (message: string) => void;
  onError: (message: string) => void;
}

const EMPTY_FORM: EducationData = {
  institution_name: "",
  degree: "",
  field_of_study: "",
  start_year: null,
  end_year: null,
  grade: "",
};

export default function EducationSection({
  accessToken,
  educations,
  onChange,
  onMessage,
  onError,
}: EducationSectionProps) {
  const [form, setForm] =
    useState<EducationData>(EMPTY_FORM);

  const [editingId, setEditingId] =
    useState<string | null>(null);

  const [isSaving, setIsSaving] =
    useState(false);

  const [deletingId, setDeletingId] =
    useState<string | null>(null);

  function resetForm() {
    setForm(EMPTY_FORM);
    setEditingId(null);
  }

  function editEducation(education: Education) {
    setEditingId(education.id);

    setForm({
      institution_name: education.institution_name,
      degree: education.degree,
      field_of_study:
        education.field_of_study ?? "",
      start_year: education.start_year,
      end_year: education.end_year,
      grade: education.grade ?? "",
    });
  }

  async function saveEducation() {
    if (
      !form.institution_name.trim() ||
      !form.degree.trim()
    ) {
      onError(
        "Institution name and degree are required.",
      );
      return;
    }

    try {
      setIsSaving(true);

      const payload: EducationData = {
        ...form,
        institution_name:
          form.institution_name.trim(),
        degree: form.degree.trim(),
      };

      if (editingId) {
        const updated =
          await updateEducation(
            accessToken,
            editingId,
            payload,
          );

        onChange(
          educations.map((education) =>
            education.id === editingId
              ? updated
              : education,
          ),
        );

        onMessage(
          "Education updated successfully.",
        );
      } else {
        const created =
          await createEducation(
            accessToken,
            payload,
          );

        onChange([...educations, created]);

        onMessage(
          "Education added successfully.",
        );
      }

      resetForm();
    } catch (error) {
      onError(
        error instanceof Error
          ? error.message
          : "Unable to save education.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  async function removeEducation(
    educationId: string,
  ) {
    if (
      !window.confirm(
        "Delete this education record?",
      )
    ) {
      return;
    }

    try {
      setDeletingId(educationId);

      await deleteEducation(
        accessToken,
        educationId,
      );

      onChange(
        educations.filter(
          (education) =>
            education.id !== educationId,
        ),
      );

      if (editingId === educationId) {
        resetForm();
      }

      onMessage(
        "Education deleted successfully.",
      );
    } catch (error) {
      onError(
        error instanceof Error
          ? error.message
          : "Unable to delete education.",
      );
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <section className="mt-8 rounded-3xl border border-slate-200 bg-white p-7 shadow-sm">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wider text-blue-600">
            Academic Background
          </p>

          <h2 className="mt-2 text-2xl font-bold text-slate-950">
            Education
          </h2>
        </div>

        {editingId && (
          <button
            type="button"
            onClick={resetForm}
            className="text-sm font-semibold text-slate-600 hover:text-slate-950"
          >
            Cancel editing
          </button>
        )}
      </div>

      {educations.length > 0 && (
        <div className="mt-6 space-y-3">
          {educations.map((education) => (
            <article
              key={education.id}
              className="rounded-2xl border border-slate-200 p-5"
            >
              <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <h3 className="font-semibold text-slate-950">
                    {education.degree}
                    {education.field_of_study
                      ? ` — ${education.field_of_study}`
                      : ""}
                  </h3>

                  <p className="mt-1 text-sm text-slate-600">
                    {education.institution_name}
                  </p>

                  {(education.start_year ||
                    education.end_year) && (
                    <p className="mt-1 text-sm text-slate-500">
                      {education.start_year ??
                        "Unknown"}{" "}
                      –{" "}
                      {education.end_year ??
                        "Present"}
                    </p>
                  )}

                  {education.grade && (
                    <p className="mt-1 text-sm text-slate-500">
                      Grade: {education.grade}
                    </p>
                  )}
                </div>

                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() =>
                      editEducation(education)
                    }
                    className="rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                  >
                    Edit
                  </button>

                  <button
                    type="button"
                    disabled={
                      deletingId === education.id
                    }
                    onClick={() =>
                      removeEducation(
                        education.id,
                      )
                    }
                    className="rounded-lg border border-red-200 px-3 py-2 text-sm font-medium text-red-600 hover:bg-red-50 disabled:opacity-50"
                  >
                    {deletingId === education.id
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
          label="Institution"
          value={form.institution_name}
          onChange={(value) =>
            setForm((current) => ({
              ...current,
              institution_name: value,
            }))
          }
        />

        <Input
          label="Degree"
          value={form.degree}
          onChange={(value) =>
            setForm((current) => ({
              ...current,
              degree: value,
            }))
          }
        />

        <Input
          label="Field of study"
          value={form.field_of_study ?? ""}
          onChange={(value) =>
            setForm((current) => ({
              ...current,
              field_of_study: value,
            }))
          }
        />

        <Input
          label="Grade / CGPA"
          value={form.grade ?? ""}
          onChange={(value) =>
            setForm((current) => ({
              ...current,
              grade: value,
            }))
          }
        />

        <NumberInput
          label="Start year"
          value={form.start_year}
          onChange={(value) =>
            setForm((current) => ({
              ...current,
              start_year: value,
            }))
          }
        />

        <NumberInput
          label="End year"
          value={form.end_year}
          onChange={(value) =>
            setForm((current) => ({
              ...current,
              end_year: value,
            }))
          }
        />
      </div>

      <div className="mt-5 flex justify-end">
        <button
          type="button"
          disabled={isSaving}
          onClick={saveEducation}
          className="rounded-xl bg-blue-600 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {isSaving
            ? "Saving..."
            : editingId
              ? "Update Education"
              : "Add Education"}
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
        className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 text-sm text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
      />
    </div>
  );
}

function NumberInput({
  label,
  value,
  onChange,
}: {
  label: string;
  value: number | null | undefined;
  onChange: (value: number | null) => void;
}) {
  return (
    <div>
      <label className="text-sm font-medium text-slate-700">
        {label}
      </label>

      <input
        type="number"
        min="1900"
        max="2100"
        value={value ?? ""}
        onChange={(event) =>
          onChange(
            event.target.value
              ? Number(event.target.value)
              : null,
          )
        }
        className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 text-sm text-slate-900 outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
      />
    </div>
  );
}