import { useEffect } from "react";
import { on } from "../ipc";
import { EVENTS } from "../types";

/** Re-run `fn` whenever the backend emits data-changed / data-imported. */
export function useDataRefresh(fn: () => void) {
  useEffect(() => {
    fn();
    const u1 = on(EVENTS.DATA_CHANGED, fn);
    const u2 = on(EVENTS.DATA_IMPORTED, fn);
    const u3 = on(EVENTS.SCHOOL_YEAR_CHANGED, fn);
    return () => {
      u1.then((f) => f());
      u2.then((f) => f());
      u3.then((f) => f());
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
}
