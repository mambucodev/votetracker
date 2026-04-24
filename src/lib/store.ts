import { create } from "zustand";
import type { SchoolYear } from "./types";

interface AppState {
  year: SchoolYear | null;
  term: 1 | 2;
  setYear: (y: SchoolYear | null) => void;
  setTerm: (t: 1 | 2) => void;

  // Page-scoped intents fired by the global shortcut / menu router. The
  // owning page consumes the flag (sets it back to false) right after
  // acting, so re-mounts don't re-trigger.
  newVoteIntent: boolean;
  exportPdfIntent: boolean;
  requestNewVote: () => void;
  requestExportPdf: () => void;
  consumeNewVote: () => void;
  consumeExportPdf: () => void;
}

export const useApp = create<AppState>((set) => ({
  year: null,
  term: 1,
  setYear: (y) => set({ year: y }),
  setTerm: (t) => set({ term: t }),
  newVoteIntent: false,
  exportPdfIntent: false,
  requestNewVote: () => set({ newVoteIntent: true }),
  requestExportPdf: () => set({ exportPdfIntent: true }),
  consumeNewVote: () => set({ newVoteIntent: false }),
  consumeExportPdf: () => set({ exportPdfIntent: false }),
}));
