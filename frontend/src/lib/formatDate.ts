/**
 * Timestamp formatting utilities.
 *
 * All helpers accept a UTC timestamp string (e.g. "2026-03-07 00:16:25.980723")
 * or a Date object, convert to the user's local timezone, and return a formatted string.
 */

const MONTHS = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];

function toDate(input: string | Date): Date {
  if (input instanceof Date) return input;
  // If the string has no timezone indicator, treat as UTC
  const s = input.trim();
  if (!s.endsWith("Z") && !s.includes("+") && !/T.*-/.test(s)) {
    return new Date(s.replace(" ", "T") + "Z");
  }
  return new Date(s.replace(" ", "T"));
}

function pad(n: number): string {
  return n < 10 ? `0${n}` : `${n}`;
}

function hour12(d: Date): { h: number; ampm: string } {
  const h24 = d.getHours();
  const ampm = h24 >= 12 ? "PM" : "AM";
  let h = h24 % 12;
  if (h === 0) h = 12;
  return { h, ampm };
}

/** e.g. "03 Mar, 2026" */
export function fmtDate(input: string | Date): string {
  const d = toDate(input);
  return `${pad(d.getDate())} ${MONTHS[d.getMonth()]}, ${d.getFullYear()}`;
}

/** e.g. "3:30PM" */
export function fmtTime(input: string | Date): string {
  const d = toDate(input);
  const { h, ampm } = hour12(d);
  return `${h}:${pad(d.getMinutes())}${ampm}`;
}

/** e.g. "3:30:45PM" */
export function fmtTimeSec(input: string | Date): string {
  const d = toDate(input);
  const { h, ampm } = hour12(d);
  return `${h}:${pad(d.getMinutes())}:${pad(d.getSeconds())}${ampm}`;
}

/** e.g. "3 Mar, 25 — 3:30PM" */
export function fmtDateTime(input: string | Date): string {
  const d = toDate(input);
  const { h, ampm } = hour12(d);
  const yr = String(d.getFullYear()).slice(-2);
  return `${d.getDate()} ${MONTHS[d.getMonth()]}, ${yr} — ${h}:${pad(d.getMinutes())}${ampm}`;
}
