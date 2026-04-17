// Mirrors src-tauri/src/domain/types.rs + src-tauri/src/events.rs
// Keep these in sync whenever the Rust shapes change.

export type GradeType = "Written" | "Oral" | "Practical";

export interface Vote {
  id: number | null;
  subject: string;
  grade: number;
  /** Rust field `kind` — serialized as `type`. */
  type: GradeType;
  term: number;
  date: string; // YYYY-MM-DD
  description: string | null;
  weight: number;
  school_year_id: number | null;
}

export interface SchoolYear {
  id: number;
  name: string;
  start_year: number;
  is_active: boolean;
}

export interface UndoState {
  can_undo: boolean;
  can_redo: boolean;
  undo_text: string | null;
  redo_text: string | null;
}

export type MappingAction = "map" | "create" | "manual";

export interface AutoSuggestion {
  suggested_match: string | null;
  confidence: number;
  suggested_new: string | null;
  action: MappingAction;
}

// ---------- Events ----------

export type SyncStatusPayload =
  | { kind: "started"; provider_id: string }
  | { kind: "progress"; provider_id: string; message: string }
  | {
      kind: "done";
      provider_id: string;
      new_count: number;
      updated_count: number;
      skipped_count: number;
    }
  | { kind: "failed"; provider_id: string; message: string };

export interface SchoolYearChangedPayload {
  school_year_id?: number;
  added?: number;
}

export const EVENTS = {
  DATA_CHANGED: "data-changed",
  DATA_IMPORTED: "data-imported",
  SCHOOL_YEAR_CHANGED: "school-year-changed",
  UNDO_STATE: "undo-state",
  SYNC_STATUS: "sync-status",
  THEME_CHANGED: "theme-changed",
} as const;
