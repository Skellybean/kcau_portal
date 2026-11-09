export const DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
export const DAY_SHORT = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

// Backend weekdays run Monday = 0; JavaScript's run Sunday = 0.
export function todayIndex() {
  return (new Date().getDay() + 6) % 7;
}

export function clock(value) {
  return value ? String(value).slice(0, 5) : "";
}

export function longDate(date = new Date()) {
  return date.toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long" });
}

export function shortDate(iso) {
  return new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

export function firstName(fullName) {
  return String(fullName || "").trim().split(/\s+/)[0] || "";
}

export function roleLabel(role) {
  return { student: "Student", lecturer: "Lecturer", admin: "Administrator" }[role] || role;
}
