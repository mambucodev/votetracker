import { create } from "zustand";
import type { SchoolYear } from "./types";

interface AppState {
  year: SchoolYear | null;
  term: 1 | 2;
  setYear: (y: SchoolYear | null) => void;
  setTerm: (t: 1 | 2) => void;
}

export const useApp = create<AppState>((set) => ({
  year: null,
  term: 1,
  setYear: (y) => set({ year: y }),
  setTerm: (t) => set({ term: t }),
}));
