"use client";

import { ChangeEvent, DragEvent, useRef, useState } from "react";
import { useRouter } from "next/navigation";

import {
  ResumeUploadResponse,
  uploadResume,
} from "@/lib/api/resumes";

const ACCESS_TOKEN_KEY = "careerpilot_access_token";

const MAX_FILE_SIZE = 5 * 1024 * 1024;

function formatFileSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }

  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function formatDate(value: string): string {
  return new Date(value).toLocaleString();
}

export default function ResumePage() {
  const router = useRouter();

  const inputRef = useRef<HTMLInputElement | null>(null);

  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("My Resume");

  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const [error, setError] = useState<string | null>(null);
  const [result, setResult] =
    useState<ResumeUploadResponse | null>(null);

  function validateFile(selectedFile: File): string | null {
    const isPdf =
      selectedFile.type === "application/pdf" ||
      selectedFile.name.toLowerCase().endsWith(".pdf");

    if (!isPdf) {
      return "Please select a PDF resume.";
    }

    if (selectedFile.size > MAX_FILE_SIZE) {
      return "The resume must be 5 MB or smaller.";
    }

    if (selectedFile.size === 0) {
      return "The selected file is empty.";
    }

    return null;
  }

  function selectFile(selectedFile: File) {
    const validationError = validateFile(selectedFile);

    if (validationError) {
      setFile(null);
      setError(validationError);
      return;
    }

    setFile(selectedFile);
    setError(null);
    setResult(null);
  }

  function handleFileChange(
    event: ChangeEvent<HTMLInputElement>,
  ) {
    const selectedFile = event.target.files?.[0];

    if (!selectedFile) {
      return;
    }

    selectFile(selectedFile);
  }

  function handleDragOver(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDragging(true);
  }

  function handleDragLeave(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDragging(false);
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDragging(false);

    const selectedFile = event.dataTransfer.files?.[0];

    if (!selectedFile) {
      return;
    }

    selectFile(selectedFile);
  }

  function clearSelectedFile() {
    setFile(null);
    setResult(null);
    setError(null);

    if (inputRef.current) {
      inputRef.current.value = "";
    }
  }

  async function handleUpload() {
    if (!file) {
      setError("Select a PDF resume before uploading.");
      return;
    }

    const trimmedTitle = title.trim();

    if (!trimmedTitle) {
      setError("Enter a title for your resume.");
      return;
    }

    const accessToken = sessionStorage.getItem(
      ACCESS_TOKEN_KEY,
    );

    if (!accessToken) {
      router.push("/login");
      return;
    }

    try {
      setIsUploading(true);
      setError(null);
      setResult(null);

      const uploadResult = await uploadResume(
        accessToken,
        file,
        trimmedTitle,
      );

      setResult(uploadResult);
    } catch (uploadError) {
      const message =
        uploadError instanceof Error
          ? uploadError.message
          : "Resume upload failed.";

      setError(message);
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-6xl px-6 py-10">
        <div className="mb-8 flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-blue-600">
              CareerPilot AI
            </p>

            <h1 className="mt-2 text-3xl font-bold text-slate-900">
              Resume Intelligence
            </h1>

            <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-600">
              Upload your resume to extract career evidence and
              connect detected skills to your CareerPilot profile.
            </p>
          </div>

          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => router.push("/dashboard")}
              className="rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-100"
            >
              Dashboard
            </button>

            <button
              type="button"
              onClick={() => router.push("/skills")}
              className="rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-slate-700"
            >
              Skills & Evidence
            </button>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-[1.3fr_0.7fr]">
          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div>
              <h2 className="text-xl font-bold text-slate-900">
                Upload Resume
              </h2>

              <p className="mt-1 text-sm text-slate-500">
                PDF only · Maximum file size 5 MB
              </p>
            </div>

            <div className="mt-6">
              <label
                htmlFor="resume-title"
                className="text-sm font-semibold text-slate-700"
              >
                Resume title
              </label>

              <input
                id="resume-title"
                type="text"
                value={title}
                onChange={(event) =>
                  setTitle(event.target.value)
                }
                disabled={isUploading}
                className="mt-2 w-full rounded-xl border border-slate-300 px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-100 disabled:bg-slate-100"
                placeholder="Example: Software Engineer Resume"
              />
            </div>

            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => {
                if (!isUploading) {
                  inputRef.current?.click();
                }
              }}
              className={`mt-6 cursor-pointer rounded-2xl border-2 border-dashed p-10 text-center transition ${
                isDragging
                  ? "border-blue-500 bg-blue-50"
                  : "border-slate-300 bg-slate-50 hover:border-blue-400 hover:bg-blue-50/50"
              }`}
            >
              <input
                ref={inputRef}
                type="file"
                accept=".pdf,application/pdf"
                onChange={handleFileChange}
                className="hidden"
                disabled={isUploading}
              />

              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-100 text-2xl">
                📄
              </div>

              <p className="mt-4 font-semibold text-slate-800">
                Drop your resume here
              </p>

              <p className="mt-1 text-sm text-slate-500">
                or click to choose a PDF from your computer
              </p>
            </div>

            {file && (
              <div className="mt-5 flex flex-col gap-4 rounded-xl border border-slate-200 bg-slate-50 p-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="min-w-0">
                  <p className="truncate text-sm font-semibold text-slate-800">
                    {file.name}
                  </p>

                  <p className="mt-1 text-xs text-slate-500">
                    {formatFileSize(file.size)}
                  </p>
                </div>

                <button
                  type="button"
                  onClick={clearSelectedFile}
                  disabled={isUploading}
                  className="text-sm font-semibold text-red-600 hover:text-red-700 disabled:opacity-50"
                >
                  Remove
                </button>
              </div>
            )}

            {error && (
              <div className="mt-5 rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                {error}
              </div>
            )}

            <button
              type="button"
              onClick={handleUpload}
              disabled={!file || isUploading}
              className="mt-6 w-full rounded-xl bg-blue-600 px-5 py-3 font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-slate-300"
            >
              {isUploading
                ? "Analyzing Resume..."
                : "Upload & Analyze Resume"}
            </button>

            <p className="mt-4 text-xs leading-5 text-slate-500">
              Resume text is used as evidence for detected skills.
              Detection alone does not automatically prove skill
              proficiency.
            </p>
          </section>

          <aside className="space-y-6">
            <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-lg font-bold text-slate-900">
                Evidence Pipeline
              </h2>

              <div className="mt-5 space-y-4">
                {[
                  ["1", "Upload", "Securely submit your PDF resume."],
                  [
                    "2",
                    "Extract",
                    "Parse resume text and relevant sections.",
                  ],
                  [
                    "3",
                    "Detect",
                    "Identify supported skills from resume evidence.",
                  ],
                  [
                    "4",
                    "Connect",
                    "Add evidence to your evolving career profile.",
                  ],
                ].map(([number, heading, description]) => (
                  <div
                    key={number}
                    className="flex gap-3"
                  >
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-100 text-sm font-bold text-blue-700">
                      {number}
                    </div>

                    <div>
                      <p className="text-sm font-semibold text-slate-800">
                        {heading}
                      </p>

                      <p className="mt-0.5 text-xs leading-5 text-slate-500">
                        {description}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <section className="rounded-2xl border border-amber-200 bg-amber-50 p-5">
              <h3 className="text-sm font-bold text-amber-900">
                Evidence-aware by design
              </h3>

              <p className="mt-2 text-xs leading-5 text-amber-800">
                CareerPilot distinguishes resume claims and detected
                evidence from measured competency. Assessment evidence
                can strengthen the career profile separately.
              </p>
            </section>
          </aside>
        </div>

        {result && (
          <section className="mt-6 rounded-2xl border border-emerald-200 bg-white p-6 shadow-sm">
            <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
              <div>
                <div className="inline-flex rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold text-emerald-700">
                  {result.version.extraction_status}
                </div>

                <h2 className="mt-3 text-xl font-bold text-slate-900">
                  Resume processed successfully
                </h2>

                <p className="mt-1 text-sm text-slate-600">
                  CareerPilot has processed the resume and connected
                  supported resume evidence to your profile.
                </p>
              </div>

              <button
                type="button"
                onClick={() => router.push("/skills")}
                className="rounded-xl bg-emerald-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-emerald-700"
              >
                View Extracted Evidence
              </button>
            </div>

            <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div className="rounded-xl bg-slate-50 p-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Resume
                </p>
                <p className="mt-2 break-words text-sm font-semibold text-slate-800">
                  {result.title}
                </p>
              </div>

              <div className="rounded-xl bg-slate-50 p-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Version
                </p>
                <p className="mt-2 text-sm font-semibold text-slate-800">
                  {result.active_version_number}
                </p>
              </div>

              <div className="rounded-xl bg-slate-50 p-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  File size
                </p>
                <p className="mt-2 text-sm font-semibold text-slate-800">
                  {formatFileSize(
                    result.version.file_size_bytes,
                  )}
                </p>
              </div>

              <div className="rounded-xl bg-slate-50 p-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Parser
                </p>
                <p className="mt-2 text-sm font-semibold text-slate-800">
                  {result.version.parser_version}
                </p>
              </div>
            </div>

            <div className="mt-4 rounded-xl border border-slate-200 p-4">
              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <p className="text-xs font-semibold text-slate-500">
                    Original filename
                  </p>
                  <p className="mt-1 break-all text-sm text-slate-800">
                    {result.version.original_filename}
                  </p>
                </div>

                <div>
                  <p className="text-xs font-semibold text-slate-500">
                    Processed at
                  </p>
                  <p className="mt-1 text-sm text-slate-800">
                    {formatDate(result.version.created_at)}
                  </p>
                </div>
              </div>
            </div>
          </section>
        )}
      </div>
    </main>
  );
}