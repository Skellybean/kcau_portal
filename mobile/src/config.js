// Backend address. Set EXPO_PUBLIC_API_URL in .env (see .env.example).
export const API_URL = (process.env.EXPO_PUBLIC_API_URL || "http://192.168.1.74:8000").replace(/\/$/, "");

// Must match KCA_STUDENT_EMAIL_DOMAINS / KCA_STAFF_EMAIL_DOMAINS on the backend.
// The server is the real gatekeeper; these only give instant feedback in the form.
export const STUDENT_EMAIL_DOMAINS = ["students.kcau.ac.ke"];
export const STAFF_EMAIL_DOMAINS = ["kcau.ac.ke"];
