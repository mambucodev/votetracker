// Typed wrappers around Tauri `invoke()` / `listen()`. Keeps React
// components free of stringly-typed command names.

import { invoke } from "@tauri-apps/api/core";
import { listen, type Event, type UnlistenFn } from "@tauri-apps/api/event";
import type {
  AutoSuggestion,
  SchoolYear,
  UndoState,
  Vote,
} from "./types";

// ---------- Votes ----------

export const listVotes = (opts?: {
  subject?: string;
  schoolYearId?: number;
  term?: number;
}) =>
  invoke<Vote[]>("list_votes", {
    subject: opts?.subject ?? null,
    schoolYearId: opts?.schoolYearId ?? null,
    term: opts?.term ?? null,
  });

export const getVote = (id: number) => invoke<Vote | null>("get_vote", { id });
export const addVote = (vote: Vote) => invoke<number>("add_vote", { vote });
export const updateVote = (id: number, vote: Vote) =>
  invoke<boolean>("update_vote", { id, vote });
export const deleteVote = (id: number) =>
  invoke<boolean>("delete_vote", { id });

// ---------- Subjects ----------

export const listSubjects = () => invoke<string[]>("list_subjects");
export const addSubject = (name: string) =>
  invoke<number>("add_subject", { name });
export const renameSubject = (oldName: string, newName: string) =>
  invoke<boolean>("rename_subject", { oldName, newName });
export const deleteSubject = (name: string) =>
  invoke<boolean>("delete_subject", { name });

// ---------- School years ----------

export const listYears = () => invoke<SchoolYear[]>("list_years");
export const activeYear = () => invoke<SchoolYear | null>("active_year");
export const addYear = (startYear: number) =>
  invoke<number>("add_year", { startYear });
export const setActiveYear = (yearId: number) =>
  invoke<void>("set_active_year", { yearId });
export const deleteYear = (yearId: number) =>
  invoke<boolean>("delete_year", { yearId });

// ---------- Settings ----------

export const getSetting = (key: string) =>
  invoke<string | null>("get_setting", { key });
export const setSetting = (key: string, value: string) =>
  invoke<void>("set_setting", { key, value });
export const getCurrentTerm = () => invoke<number>("get_current_term");
export const setCurrentTerm = (term: number) =>
  invoke<void>("set_current_term", { term });

// ---------- Domain helpers ----------

export const calculateNeededGrade = (opts: {
  subject?: string;
  targetAvg: number;
  newWeight: number;
  schoolYearId?: number;
  term?: number;
}) =>
  invoke<number | null>("calculate_needed_grade", {
    subject: opts.subject ?? null,
    targetAvg: opts.targetAvg,
    newWeight: opts.newWeight,
    schoolYearId: opts.schoolYearId ?? null,
    term: opts.term ?? null,
  });

export const subjectMappingSuggestion = (sourceSubject: string) =>
  invoke<AutoSuggestion>("subject_mapping_suggestion", { sourceSubject });

export const saveProviderMapping = (
  providerId: string,
  sourceSubject: string,
  targetSubject: string,
) =>
  invoke<void>("save_provider_mapping", {
    providerId,
    sourceSubject,
    targetSubject,
  });

export const listProviderMappings = (providerId: string) =>
  invoke<Record<string, string>>("list_provider_mappings", { providerId });

// ---------- Undo / redo ----------

export const undoState = () => invoke<UndoState>("undo_state");
export const undo = () => invoke<boolean>("undo");
export const redo = () => invoke<boolean>("redo");

// ---------- Event subscriptions ----------

export function on<T>(
  event: string,
  handler: (payload: T) => void,
): Promise<UnlistenFn> {
  return listen<T>(event, (e: Event<T>) => handler(e.payload));
}
