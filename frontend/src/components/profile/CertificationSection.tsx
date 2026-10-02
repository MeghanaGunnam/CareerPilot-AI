"use client";

import { useState } from "react";

import {
  createCertification,
  updateCertification,
  deleteCertification,
  type Certification,
  type CertificationData,
} from "@/lib/api/students";

interface Props {
  accessToken: string;
  certifications: Certification[];
  onChange: (items: Certification[]) => void;
  onMessage: (message: string) => void;
  onError: (message: string) => void;
}

const EMPTY_FORM: CertificationData = {
  name: "",
  issuing_organization: "",
  issue_date: null,
  expiration_date: null,
  credential_id: "",
  credential_url: "",
  description: "",
};

export default function CertificationSection({
  accessToken,
  certifications,
  onChange,
  onMessage,
  onError,
}: Props) {
  const [form, setForm] =
    useState<CertificationData>(EMPTY_FORM);

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

  function edit(item: Certification) {
    setEditingId(item.id);

    setForm({
      name: item.name,
      issuing_organization:
        item.issuing_organization,
      issue_date: item.issue_date,
      expiration_date: item.expiration_date,
      credential_id: item.credential_id ?? "",
      credential_url: item.credential_url ?? "",
      description: item.description ?? "",
    });
  }

  async function save() {
    if (
      !form.name.trim() ||
      !form.issuing_organization.trim()
    ) {
      onError(
        "Certification name and issuing organization are required.",
      );
      return;
    }

    try {
      setIsSaving(true);

      const payload: CertificationData = {
        ...form,
        name: form.name.trim(),
        issuing_organization:
          form.issuing_organization.trim(),
      };

      if (editingId) {
        const updated =
          await updateCertification(
            accessToken,
            editingId,
            payload,
          );

        onChange(
          certifications.map((item) =>
            item.id === editingId
              ? updated
              : item,
          ),
        );

        onMessage(
          "Certification updated successfully.",
        );
      } else {
        const created =
          await createCertification(
            accessToken,
            payload,
          );

        onChange([
          ...certifications,
          created,
        ]);

        onMessage(
          "Certification added successfully.",
        );
      }

      reset();
    } catch (error) {
      onError(
        error instanceof Error
          ? error.message
          : "Unable to save certification.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  async function remove(id: string) {
    if (
      !window.confirm(
        "Delete this certification?",
      )
    ) {
      return;
    }

    try {
      setDeletingId(id);

      await deleteCertification(
        accessToken,
        id,
      );

      onChange(
        certifications.filter(
          (item) => item.id !== id,
        ),
      );

      if (editingId === id) {
        reset();
      }

      onMessage(
        "Certification deleted successfully.",
      );
    } catch (error) {
      onError(
        error instanceof Error
          ? error.message
          : "Unable to delete certification.",
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
            Credentials
          </p>

          <h2 className="mt-2 text-2xl font-bold text-slate-950">
            Certifications
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

      {certifications.length > 0 && (
        <div className="mt-6 space-y-3">
          {certifications.map((item) => (
            <article
              key={item.id}
              className="rounded-2xl border border-slate-200 p-5"
            >
              <div className="flex flex-col justify-between gap-4 sm:flex-row">
                <div>
                  <h3 className="font-semibold text-slate-950">
                    {item.name}
                  </h3>

                  <p className="mt-1 text-sm text-slate-600">
                    {item.issuing_organization}
                  </p>

                  {item.issue_date && (
                    <p className="mt-1 text-sm text-slate-500">
                      Issued: {item.issue_date}
                    </p>
                  )}

                  {item.credential_id && (
                    <p className="mt-1 text-sm text-slate-500">
                      Credential ID:{" "}
                      {item.credential_id}
                    </p>
                  )}

                  {item.credential_url && (
                    <a
                      href={item.credential_url}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-2 inline-block text-sm font-medium text-blue-600"
                    >
                      View credential
                    </a>
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
          label="Certification name"
          value={form.name}
          onChange={(value) =>
            setForm((old) => ({
              ...old,
              name: value,
            }))
          }
        />

        <Input
          label="Issuing organization"
          value={form.issuing_organization}
          onChange={(value) =>
            setForm((old) => ({
              ...old,
              issuing_organization: value,
            }))
          }
        />

        <DateInput
          label="Issue date"
          value={form.issue_date ?? ""}
          onChange={(value) =>
            setForm((old) => ({
              ...old,
              issue_date: value || null,
            }))
          }
        />

        <DateInput
          label="Expiration date"
          value={form.expiration_date ?? ""}
          onChange={(value) =>
            setForm((old) => ({
              ...old,
              expiration_date: value || null,
            }))
          }
        />

        <Input
          label="Credential ID"
          value={form.credential_id ?? ""}
          onChange={(value) =>
            setForm((old) => ({
              ...old,
              credential_id: value,
            }))
          }
        />

        <Input
          label="Credential URL"
          value={form.credential_url ?? ""}
          onChange={(value) =>
            setForm((old) => ({
              ...old,
              credential_url: value,
            }))
          }
        />
      </div>

      <div className="mt-5">
        <label className="text-sm font-medium text-slate-700">
          Description
        </label>

        <textarea
          rows={3}
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
              ? "Update Certification"
              : "Add Certification"}
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