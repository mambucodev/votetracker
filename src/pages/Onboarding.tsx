import { useEffect, useState } from "react";
import { Button } from "@/components/primitives/Button";
import { Field, TextInput } from "@/components/primitives/Field";
import { addSubject, listSubjects, setSetting } from "@/lib/ipc";
import { PRESET_SUBJECTS, tr } from "@/lib/i18n";
import "./Onboarding.scss";

interface Props {
  onDone: () => void;
}

export default function Onboarding({ onDone }: Props) {
  const [step, setStep] = useState(0);
  const [picks, setPicks] = useState<Record<string, boolean>>({});
  const [custom, setCustom] = useState("");
  const [existing, setExisting] = useState<string[]>([]);

  useEffect(() => {
    listSubjects().then(setExisting).catch(console.error);
  }, []);

  async function finish() {
    for (const [name, on] of Object.entries(picks)) {
      if (!on) continue;
      if (!existing.includes(name)) await addSubject(name);
    }
    if (custom.trim()) await addSubject(custom.trim());
    await setSetting("onboarding_complete", "1");
    onDone();
  }

  return (
    <div className="onboarding">
      <div className="ob-card">
        <div className="step-indicator">
          {["Welcome", "Subjects", "Provider", "Done"].map((s, i) => (
            <span key={s} className={i <= step ? "active" : ""}>
              {s}
            </span>
          ))}
        </div>

        {step === 0 && (
          <>
            <h2>{tr("Welcome to VoteTracker")}</h2>
            <p className="muted">
              Track grades, simulate report cards, and sync from Italian electronic
              registers. Let's set up the basics in under a minute.
            </p>
          </>
        )}

        {step === 1 && (
          <>
            <h2>{tr("Add subjects")}</h2>
            <div className="preset-grid">
              {PRESET_SUBJECTS.map((s) => (
                <label key={s} className="chip">
                  <input
                    type="checkbox"
                    checked={!!picks[s]}
                    onChange={(e) =>
                      setPicks({ ...picks, [s]: e.target.checked })
                    }
                  />
                  {s}
                </label>
              ))}
            </div>
            <Field label="Custom">
              <TextInput
                placeholder="E.g. Economics"
                value={custom}
                onChange={(e) => setCustom(e.target.value)}
              />
            </Field>
          </>
        )}

        {step === 2 && (
          <>
            <h2>{tr("Connect a provider (optional)")}</h2>
            <p className="muted">
              You can import grades from ClasseViva or Axios. Configure providers
              later from Settings → Sync Providers.
            </p>
          </>
        )}

        {step === 3 && (
          <>
            <h2>{tr("You're all set")}</h2>
            <p className="muted">
              Jump in and add your first grade with Ctrl+N on the Votes page, or
              let a provider sync pull them in automatically.
            </p>
          </>
        )}

        <div className="ob-actions">
          {step > 0 && (
            <Button variant="ghost" onClick={() => setStep(step - 1)}>
              {tr("Back")}
            </Button>
          )}
          <div style={{ flex: 1 }} />
          {step < 3 && (
            <Button variant="primary" onClick={() => setStep(step + 1)}>
              {tr("Next")}
            </Button>
          )}
          {step === 3 && (
            <Button variant="primary" onClick={finish}>
              {tr("Finish")}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
