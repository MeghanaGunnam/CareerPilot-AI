export const NAVIGATION = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/profile", label: "Profile" },
  { href: "/resume", label: "Resume" },
  { href: "/skills", label: "Skills & Evidence" },
  { href: "/assessment", label: "Assessments" },
  { href: "/roadmap", label: "Learning Roadmap" },
  { href: "/certifications", label: "Recommended Certifications" },
  { href: "/job-match", label: "Job Match" },
  { href: "/applications", label: "Applications" },
  { href: "/progress", label: "Progress" },
  { href: "/assistant", label: "AI Assistant" },
] as const;

export function activeDestination(path: string): string | null {
  if (path === "/evidence") return "/skills";
  return NAVIGATION.find((item) => path === item.href || path.startsWith(item.href + "/"))?.href ?? null;
}
