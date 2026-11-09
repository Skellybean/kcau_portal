import { STAFF_EMAIL_DOMAINS, STUDENT_EMAIL_DOMAINS } from "../config";

export const KCA_EMAIL_MESSAGE =
  "Use your KCA email: students.kcau.ac.ke for students, kcau.ac.ke for lecturers.";

// Exact match on the text after the single "@", so look-alike domains are rejected.
export function classifyEmail(value) {
  const email = String(value || "").trim().toLowerCase();
  const parts = email.split("@");
  if (parts.length !== 2 || !parts[0] || !parts[1]) return null;
  if (STUDENT_EMAIL_DOMAINS.includes(parts[1])) return "student";
  if (STAFF_EMAIL_DOMAINS.includes(parts[1])) return "lecturer";
  return null;
}

export function emailError(value) {
  if (!String(value || "").trim()) return "Enter your KCA email address.";
  return classifyEmail(value) ? null : KCA_EMAIL_MESSAGE;
}
