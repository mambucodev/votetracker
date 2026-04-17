import { en } from "./en";
import { it } from "./it";

export type Lang = "en" | "it";
const maps: Record<Lang, Record<string, string>> = { en, it };

let current: Lang = detect();

function detect(): Lang {
  if (typeof navigator === "undefined") return "en";
  return navigator.language?.toLowerCase().startsWith("it") ? "it" : "en";
}

export function setLang(l: Lang) {
  current = l;
}
export function getLang(): Lang {
  return current;
}

export function tr(key: string): string {
  return maps[current][key] ?? key;
}

export const PRESET_SUBJECTS = [
  "Italian",
  "Math",
  "English",
  "History",
  "Philosophy",
  "Physics",
  "Science",
  "Latin",
  "Art",
  "Physical Education",
  "Computer Science",
  "Religion",
  "Geography",
  "Chemistry",
  "Biology",
];
