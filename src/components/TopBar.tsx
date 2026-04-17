import { useEffect, useState } from "react";
import { Undo2, Redo2 } from "lucide-react";
import { undo, redo, setCurrentTerm as setCurTerm, undoState } from "@/lib/ipc";
import { useApp } from "@/lib/store";
import { on } from "@/lib/ipc";
import { EVENTS, type UndoState } from "@/lib/types";
import { Button } from "./primitives/Button";
import { tr } from "@/lib/i18n";
import "./TopBar.scss";

interface Props {
  title: string;
  right?: React.ReactNode;
}

export function TopBar({ title, right }: Props) {
  const { term, setTerm } = useApp();
  const [undoSt, setUndoSt] = useState<UndoState>({
    can_undo: false,
    can_redo: false,
    undo_text: null,
    redo_text: null,
  });

  useEffect(() => {
    undoState().then(setUndoSt).catch(() => {});
    const u = on<UndoState>(EVENTS.UNDO_STATE, setUndoSt);
    return () => {
      u.then((f) => f());
    };
  }, []);

  async function onTerm(t: 1 | 2) {
    setTerm(t);
    await setCurTerm(t);
  }

  return (
    <header className="topbar">
      <h1 className="topbar-title">{tr(title)}</h1>
      <div className="topbar-tools">
        <div className="term-switch" role="tablist">
          <button
            role="tab"
            aria-selected={term === 1}
            className={`pill ${term === 1 ? "active" : ""}`}
            onClick={() => onTerm(1)}
          >
            1
          </button>
          <button
            role="tab"
            aria-selected={term === 2}
            className={`pill ${term === 2 ? "active" : ""}`}
            onClick={() => onTerm(2)}
          >
            2
          </button>
        </div>
        <Button
          variant="ghost"
          size="sm"
          disabled={!undoSt.can_undo}
          title={`${undoSt.undo_text ?? "Undo"} • Ctrl+Z`}
          onClick={() => undo().catch(() => {})}
        >
          <Undo2 size={14} strokeWidth={1.75} />
        </Button>
        <Button
          variant="ghost"
          size="sm"
          disabled={!undoSt.can_redo}
          title={`${undoSt.redo_text ?? "Redo"} • Ctrl+Shift+Z`}
          onClick={() => redo().catch(() => {})}
        >
          <Redo2 size={14} strokeWidth={1.75} />
        </Button>
        {right}
      </div>
    </header>
  );
}
