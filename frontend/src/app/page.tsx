"use client";

import { useState } from "react";

export default function Home() {
  const [result, setResult] = useState("Not tested yet");

  async function testBackend() {
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/health`
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();

      setResult(JSON.stringify(data, null, 2));
    } catch (error) {
      setResult(
        error instanceof Error
          ? error.message
          : "Backend connection failed"
      );
    }
  }

  return (
    <main className="min-h-screen p-10">
      <h1 className="text-3xl font-bold">
        CareerPilot AI
      </h1>

      <p className="mt-3">
        Frontend → Backend connection test
      </p>

      <button
        onClick={testBackend}
        className="mt-6 rounded-lg bg-black px-5 py-3 text-white"
      >
        Test Backend
      </button>

      <pre className="mt-6 rounded-lg bg-gray-100 p-4">
        {result}
      </pre>
    </main>
  );
}