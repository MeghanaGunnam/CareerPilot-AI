"use client";

import { FormEvent, useState } from "react";

import { ApiError } from "@/lib/api/client";
import {
  createCertification,
  deleteCertification,
  type Certification,
  type CertificationData,
} from "@/lib/api/students";

interface CertificationStepProps {
  accessToken: string;
  certifications: Certification[];
  setCertifications: (
    value:
      | Certification[]
      | ((
          current: Certification[]
        ) => Certification[])
  ) => void;
  onBack: () => void;
  onContinue: () => void;
}

const emptyCertification: CertificationData = {
  name: "",
  issuing_organization: "",
  issue_date: null,
  expiration_date: null,
  credential_id: "",
  credential_url: "",
  description: "",
};

export default function CertificationStep({
  accessToken,
  certifications,
  setCertifications,
  onBack,
  onContinue,
}: CertificationStepProps) {
  const [formData, setFormData] =
    useState<CertificationData>(
      emptyCertification
    );

  const [isSaving, setIsSaving] =
    useState(false);

  const [error, setError] = useState("");

  function updateField(
    field: keyof CertificationData,
    value: string | null
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
      const savedCertification =
        await createCertification(
          accessToken,
          formData
        );

      setCertifications((current) => [
        ...current,
        savedCertification,
      ]);

      setFormData(emptyCertification);
    } catch (error) {
      if (error instanceof ApiError) {
        setError(error.message);
      } else {
        setError(
          "Unable to save certification."
        );
      }
    } finally {
      setIsSaving(false);
    }
  }

  async function handleDelete(id: string) {
    setError("");

    try {
      await deleteCertification(
        accessToken,
        id
      );

      setCertifications((current) =>
        current.filter(
          (certification) =>
            certification.id !== id
        )
      );
    } catch (error) {
      if (error instanceof ApiError) {
        setError(error.message);
      } else {
        setError(
          "Unable to delete certification."
        );
      }
    }
  }

  return (
    <>
      <div className="border-b border-slate-200 pb-6">
        <p className="text-sm font-medium text-blue-600">
          Step 5 of 6
        </p>

        <h2 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">
          Certifications
        </h2>

        <p className="mt-3 max-w-2xl text-slate-600">
          Add certifications that provide
          evidence of your learning and skills.
          This step is optional.
        </p>
      </div>

      {certifications.length > 0 && (
        <div className="mt-8 space-y-3">
          <p className="text-sm font-semibold text-slate-700">
            Added certifications
          </p>

          {certifications.map(
            (certification) => (
              <div
                key={certification.id}
                className="flex items-start justify-between gap-4 rounded-xl border border-slate-200 bg-slate-50 p-4"
              >
                <div>
                  <p className="font-semibold text-slate-950">
                    {certification.name}
                  </p>

                  <p className="mt-1 text-sm text-slate-600">
                    {
                      certification.issuing_organization
                    }
                  </p>

                  {certification.issue_date && (
                    <p className="mt-2 text-xs text-slate-500">
                      Issued{" "}
                      {formatDate(
                        certification.issue_date
                      )}
                    </p>
                  )}

                  {certification.credential_id && (
                    <p className="mt-1 text-xs text-slate-500">
                      Credential:{" "}
                      {
                        certification.credential_id
                      }
                    </p>
                  )}
                </div>

                <button
                  type="button"
                  onClick={() =>
                    handleDelete(
                      certification.id
                    )
                  }
                  className="text-sm font-medium text-red-600 hover:text-red-700"
                >
                  Remove
                </button>
              </div>
            )
          )}
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        className="mt-8"
      >
        <div className="grid gap-6 md:grid-cols-2">
          <Input
            id="certification-name"
            label="Certification name"
            required
            value={formData.name}
            placeholder="AWS Cloud Practitioner"
            onChange={(value) =>
              updateField("name", value)
            }
          />

          <Input
            id="issuing-organization"
            label="Issuing organization"
            required
            value={
              formData.issuing_organization
            }
            placeholder="Amazon Web Services"
            onChange={(value) =>
              updateField(
                "issuing_organization",
                value
              )
            }
          />

          <Input
            id="issue-date"
            label="Issue date"
            type="date"
            value={formData.issue_date ?? ""}
            onChange={(value) =>
              updateField(
                "issue_date",
                value || null
              )
            }
          />

          <Input
            id="expiration-date"
            label="Expiration date"
            type="date"
            value={
              formData.expiration_date ?? ""
            }
            onChange={(value) =>
              updateField(
                "expiration_date",
                value || null
              )
            }
          />

          <Input
            id="credential-id"
            label="Credential ID"
            value={
              formData.credential_id ?? ""
            }
            onChange={(value) =>
              updateField(
                "credential_id",
                value
              )
            }
          />

          <Input
            id="credential-url"
            label="Credential URL"
            type="url"
            value={
              formData.credential_url ?? ""
            }
            onChange={(value) =>
              updateField(
                "credential_url",
                value
              )
            }
          />

          <div className="md:col-span-2">
            <label
              htmlFor="certification-description"
              className="mb-2 block text-sm font-medium text-slate-700"
            >
              Description
            </label>

            <textarea
              id="certification-description"
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
                : "Add certification"}
            </button>

            <button
              type="button"
              onClick={onContinue}
              className={primaryButton}
            >
              {certifications.length === 0
                ? "I have no certifications — Continue"
                : "Continue"}
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
}: {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
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
        type={type}
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