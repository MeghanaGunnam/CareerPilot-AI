export function hasAssessmentEvidence(evidence: readonly { source_type: string; evidence_strength: number | null }[]): boolean {
  return evidence.some((item) => item.source_type.toUpperCase() === "ASSESSMENT" && item.evidence_strength !== null);
}
