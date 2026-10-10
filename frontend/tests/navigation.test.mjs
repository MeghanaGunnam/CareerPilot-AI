import assert from "node:assert/strict";
import { readFileSync, existsSync } from "node:fs";
import test from "node:test";
import ts from "typescript";

async function loadTypeScript(relative) {
  const source = readFileSync(new URL(relative, import.meta.url), "utf8");
  const output = ts.transpileModule(source, { compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ES2022 } }).outputText;
  return import(`data:text/javascript;base64,${Buffer.from(output).toString("base64")}`);
}

const { NAVIGATION, activeDestination } = await loadTypeScript("../src/lib/navigation.ts");
const { hasAssessmentEvidence } = await loadTypeScript("../src/lib/evidence-display.ts");

test("all eleven major destinations are unique existing Next routes", () => {
  const expected = ["/dashboard", "/profile", "/resume", "/skills", "/assessment", "/roadmap", "/certifications", "/job-match", "/applications", "/progress", "/assistant"];
  assert.deepEqual(NAVIGATION.map((item) => item.href), expected);
  assert.equal(new Set(NAVIGATION.map((item) => item.href)).size, expected.length);
  for (const item of NAVIGATION) {
    assert.ok(existsSync(new URL(`../src/app${item.href}/page.tsx`, import.meta.url)), item.href);
    assert.equal(activeDestination(item.href), item.href);
  }
});

test("nested assessment and legacy evidence use the same canonical navigation", () => {
  assert.equal(activeDestination("/assessment/riasec/results"), "/assessment");
  assert.equal(activeDestination("/evidence"), "/skills");
  for (const path of ["/login", "/register", "/", "/assessment-unknown", "/not-found"]) assert.equal(activeDestination(path), null);
});

test("assessment evidence cannot be inferred from resume strength or timestamps", () => {
  assert.equal(hasAssessmentEvidence([]), false);
  assert.equal(hasAssessmentEvidence([{ source_type: "RESUME", evidence_strength: 1 }]), false);
  assert.equal(hasAssessmentEvidence([{ source_type: "ASSESSMENT", evidence_strength: null }]), false);
  assert.equal(hasAssessmentEvidence([{ source_type: "ASSESSMENT", evidence_strength: 0 }]), true);
});

test("new shared navigation/dashboard has no hard-coded test career", () => {
  for (const file of ["src/lib/navigation.ts", "src/components/AppNavigation.tsx", "src/app/dashboard/ModuleSummary.tsx", "src/app/dashboard/page.tsx"]) {
    const content = readFileSync(new URL(`../${file}`, import.meta.url), "utf8");
    assert.doesNotMatch(content, /Machine Learning Engineer|Data Scientists|15-2051\.00/);
  }
});
