import { useEffect, useState } from "react";
import { Modal } from "../primitives/Modal";
import { Button } from "../primitives/Button";
import "./ShortcutsHelpDialog.scss";

interface Shortcut {
  keys: string[];
  description: string;
}

interface Section {
  title: string;
  shortcuts: Shortcut[];
}

// Canonical matrix — mirrors docs/REWRITE_SPEC.md §6 and the accelerators
// declared in src-tauri/src/menu.rs. Keep the three in sync.
const SECTIONS: Section[] = [
  {
    title: "Navigation",
    shortcuts: [
      { keys: ["Ctrl", "1"], description: "Dashboard" },
      { keys: ["Ctrl", "2"], description: "Votes" },
      { keys: ["Ctrl", "3"], description: "Subjects" },
      { keys: ["Ctrl", "4"], description: "Simulator" },
      { keys: ["Ctrl", "5"], description: "Calendar" },
      { keys: ["Ctrl", "6"], description: "Report card" },
      { keys: ["Ctrl", "7"], description: "Statistics" },
      { keys: ["Ctrl", "8"], description: "Settings" },
      { keys: ["PgUp"], description: "Previous page" },
      { keys: ["PgDn"], description: "Next page" },
    ],
  },
  {
    title: "Editing",
    shortcuts: [
      { keys: ["Ctrl", "N"], description: "New vote" },
      { keys: ["Ctrl", "Z"], description: "Undo" },
      { keys: ["Ctrl", "Shift", "Z"], description: "Redo" },
      { keys: ["Ctrl", "Y"], description: "Redo (alt)" },
      { keys: ["Enter"], description: "Edit selected vote" },
      { keys: ["Delete"], description: "Delete selected vote" },
    ],
  },
  {
    title: "Data",
    shortcuts: [
      { keys: ["Ctrl", "I"], description: "Import JSON" },
      { keys: ["Ctrl", "E"], description: "Export JSON" },
      { keys: ["Ctrl", "R"], description: "Sync now" },
    ],
  },
  {
    title: "View",
    shortcuts: [
      { keys: ["Ctrl", "Shift", "T"], description: "Toggle theme" },
      { keys: ["1"], description: "Report card: first term" },
      { keys: ["2"], description: "Report card: second term" },
      { keys: ["?"], description: "Show this help" },
    ],
  },
];

export function ShortcutsHelpDialog() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onOpen = () => setOpen(true);
    window.addEventListener("vt:shortcuts-help", onOpen);
    return () => window.removeEventListener("vt:shortcuts-help", onOpen);
  }, []);

  const close = () => setOpen(false);

  return (
    <Modal
      open={open}
      onClose={close}
      title="Keyboard shortcuts"
      width={620}
      footer={
        <Button onClick={close} variant="primary">
          Close
        </Button>
      }
    >
      <div className="shortcuts-help">
        {SECTIONS.map((section) => (
          <section key={section.title} className="shortcuts-help__section">
            <h3 className="shortcuts-help__title">{section.title}</h3>
            <dl className="shortcuts-help__grid">
              {section.shortcuts.map((s) => (
                <div className="shortcuts-help__row" key={s.description}>
                  <dt className="shortcuts-help__keys">
                    {s.keys.map((k, i) => (
                      <span key={i}>
                        <kbd>{k}</kbd>
                        {i < s.keys.length - 1 && (
                          <span className="shortcuts-help__plus">+</span>
                        )}
                      </span>
                    ))}
                  </dt>
                  <dd className="shortcuts-help__desc">{s.description}</dd>
                </div>
              ))}
            </dl>
          </section>
        ))}
      </div>
    </Modal>
  );
}
