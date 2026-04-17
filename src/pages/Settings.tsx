import { useEffect, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { open as openDialog, save } from "@tauri-apps/plugin-dialog";
import { readTextFile, writeTextFile } from "@tauri-apps/plugin-fs";
import { TopBar } from "@/components/TopBar";
import { Button } from "@/components/primitives/Button";
import { ConfirmDialog } from "@/components/primitives/ConfirmDialog";
import { Field, NumberInput, Select, TextInput } from "@/components/primitives/Field";
import {
  activeYear,
  addYear,
  deleteYear,
  getSetting,
  listSubjects,
  listVotes,
  listYears,
  setActiveYear,
  setSetting,
} from "@/lib/ipc";
import { useApp } from "@/lib/store";
import { useTheme, type ThemePref } from "@/theme/ThemeProvider";
import { getLang, setLang, tr, type Lang } from "@/lib/i18n";
import type { SchoolYear, Vote } from "@/lib/types";
import "./Settings.scss";

interface ProviderDescriptor {
  id: string;
  name: string;
  fields: { name: string; label: string; type: "text" | "password" }[];
}

const PROVIDERS: ProviderDescriptor[] = [
  {
    id: "classeviva",
    name: "ClasseViva",
    fields: [
      { name: "username", label: "Username (S-code)", type: "text" },
      { name: "password", label: "Password", type: "password" },
    ],
  },
  {
    id: "axios",
    name: "Axios",
    fields: [
      { name: "customer_id", label: "Customer ID / Codice scuola", type: "text" },
      { name: "username", label: "Email / Username", type: "text" },
      { name: "password", label: "Password", type: "password" },
    ],
  },
];

export default function Settings() {
  const { year } = useApp();
  const { preference, setPreference } = useTheme();
  const [years, setYears] = useState<SchoolYear[]>([]);
  const [newYear, setNewYear] = useState(new Date().getFullYear());
  const [lang, setLangState] = useState<Lang>(getLang());
  const [yearToDelete, setYearToDelete] = useState<number | null>(null);

  useEffect(() => {
    listYears().then(setYears).catch(console.error);
  }, [year?.id]);

  async function importJson() {
    const path = await openDialog({
      multiple: false,
      filters: [{ name: "JSON", extensions: ["json"] }],
    });
    if (!path || Array.isArray(path)) return;
    try {
      const content = await readTextFile(path);
      const parsed = JSON.parse(content);
      const list = Array.isArray(parsed) ? parsed : (parsed.votes ?? parsed.voti ?? []);
      await invoke("import_votes_json", { records: list });
    } catch (e) {
      console.error(e);
      alert(`Import failed: ${e}`);
    }
  }

  async function exportJson() {
    const path = await save({
      defaultPath: "votetracker-export.json",
      filters: [{ name: "JSON", extensions: ["json"] }],
    });
    if (!path) return;
    const votes: Vote[] = await listVotes({});
    const subjects = await listSubjects();
    const doc = {
      version: "3.0",
      subjects,
      votes: votes.map((v) => ({
        subject: v.subject,
        grade: v.grade,
        type: v.type,
        term: v.term,
        date: v.date,
        description: v.description,
        weight: v.weight,
      })),
    };
    await writeTextFile(path, JSON.stringify(doc, null, 2));
  }

  async function changeLang(v: Lang) {
    setLangState(v);
    setLang(v);
    await setSetting("language", v);
  }

  async function changeTheme(v: ThemePref) {
    setPreference(v);
    await setSetting("theme_preference", v);
  }

  async function addNewYear() {
    await addYear(newYear);
    const ys = await listYears();
    setYears(ys);
  }

  function removeYear(id: number) {
    setYearToDelete(id);
  }

  async function confirmRemoveYear() {
    if (yearToDelete == null) return;
    await deleteYear(yearToDelete);
    setYearToDelete(null);
    setYears(await listYears());
  }

  async function activate(id: number) {
    await setActiveYear(id);
    const a = await activeYear();
    if (a) {
      /* propagate via store handled elsewhere */
    }
    setYears(await listYears());
  }

  return (
    <>
      <TopBar title="Settings" />
      <section className="page-content settings">
        <div className="section">
          <h3>General</h3>
          <div className="row">
            <Field label={tr("Theme")}>
              <Select
                value={preference}
                onChange={(e) => changeTheme(e.target.value as ThemePref)}
              >
                <option value="system">{tr("System")}</option>
                <option value="light">{tr("Light")}</option>
                <option value="dark">{tr("Dark")}</option>
              </Select>
            </Field>
            <Field label={tr("Language")}>
              <Select value={lang} onChange={(e) => changeLang(e.target.value as Lang)}>
                <option value="en">English</option>
                <option value="it">Italiano</option>
              </Select>
            </Field>
          </div>
        </div>

        <div className="section">
          <h3>Data</h3>
          <div className="row">
            <Button variant="secondary" onClick={importJson}>
              {tr("Import JSON")}
            </Button>
            <Button variant="secondary" onClick={exportJson}>
              {tr("Export JSON")}
            </Button>
            <Button
              variant="ghost"
              onClick={() => invoke("open_data_dir").catch(console.error)}
            >
              {tr("Open Data Folder")}
            </Button>
          </div>
        </div>

        <div className="section">
          <h3>{tr("School Years")}</h3>
          <div className="row align-end">
            <Field label="Start year">
              <NumberInput
                value={newYear}
                min={2000}
                max={2100}
                onChange={(e) => setNewYear(parseInt(e.target.value, 10))}
              />
            </Field>
            <Button variant="primary" onClick={addNewYear}>
              {tr("Add year")}
            </Button>
          </div>
          <div className="year-list">
            {years.map((y) => (
              <div key={y.id} className="year-row">
                <input
                  type="radio"
                  checked={y.is_active}
                  onChange={() => activate(y.id)}
                />
                <span>{y.name}</span>
                <div style={{ flex: 1 }} />
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => removeYear(y.id)}
                >
                  ×
                </Button>
              </div>
            ))}
          </div>
        </div>

        <div className="section">
          <h3>{tr("Sync Providers")}</h3>
          {PROVIDERS.map((p) => (
            <ProviderPanel key={p.id} provider={p} />
          ))}
        </div>
      </section>
      <ConfirmDialog
        open={yearToDelete != null}
        title={tr("Delete year?")}
        body={tr("Grades in this year will be removed.")}
        confirmLabel={tr("Delete")}
        cancelLabel={tr("Cancel")}
        danger
        onConfirm={confirmRemoveYear}
        onClose={() => setYearToDelete(null)}
      />
    </>
  );
}

function ProviderPanel({ provider }: { provider: ProviderDescriptor }) {
  const [creds, setCreds] = useState<Record<string, string>>({});
  const [autoSync, setAuto] = useState(false);
  const [interval, setInterval] = useState(60);
  const [lastSync, setLastSync] = useState<string | null>(null);
  const [status, setStatus] = useState<string>("");

  useEffect(() => {
    (async () => {
      const loaded: Record<string, string> = {};
      for (const f of provider.fields) {
        const key = `${provider.id}_${f.name}`;
        const raw = await getSetting(key);
        if (raw) {
          try {
            loaded[f.name] = atob(raw);
          } catch {
            loaded[f.name] = "";
          }
        } else {
          loaded[f.name] = "";
        }
      }
      setCreds(loaded);
      setAuto((await getSetting(`${provider.id}_auto_sync`)) === "1");
      const iv = await getSetting(`${provider.id}_sync_interval`);
      if (iv) setInterval(parseInt(iv, 10));
      setLastSync(await getSetting(`${provider.id}_last_sync`));
    })().catch(console.error);
  }, [provider.id, provider.fields]);

  async function saveCreds() {
    for (const f of provider.fields) {
      const k = `${provider.id}_${f.name}`;
      await setSetting(k, btoa(creds[f.name] ?? ""));
    }
    await setSetting(`${provider.id}_auto_sync`, autoSync ? "1" : "0");
    await setSetting(`${provider.id}_sync_interval`, String(interval));
    setStatus("Saved.");
  }

  async function syncNow() {
    try {
      setStatus("Syncing…");
      const result = await invoke<{
        new_count: number;
        updated_count: number;
        skipped_count: number;
      }>("trigger_sync_now", { providerId: provider.id });
      setStatus(
        `${result.new_count} new, ${result.updated_count} updated (${result.skipped_count} skipped)`,
      );
      setLastSync(new Date().toISOString());
    } catch (e) {
      setStatus(`Failed: ${e}`);
    }
  }

  return (
    <div className="provider-panel">
      <div className="pp-title">{provider.name}</div>
      <div className="pp-grid">
        {provider.fields.map((f) => (
          <Field key={f.name} label={f.label}>
            <TextInput
              type={f.type}
              value={creds[f.name] ?? ""}
              onChange={(e) =>
                setCreds({ ...creds, [f.name]: e.target.value })
              }
            />
          </Field>
        ))}
      </div>
      <div className="row align-end pp-controls">
        <label className="auto-sync">
          <input
            type="checkbox"
            checked={autoSync}
            onChange={(e) => setAuto(e.target.checked)}
          />
          {tr("Auto sync")}
        </label>
        <Field label={tr("Sync interval (minutes)")}>
          <NumberInput
            value={interval}
            min={5}
            max={1440}
            step={5}
            onChange={(e) => setInterval(parseInt(e.target.value, 10))}
          />
        </Field>
        <div className="pp-last">
          {tr("Last sync")}:{" "}
          <strong>{lastSync ?? tr("Never")}</strong>
        </div>
        <div style={{ flex: 1 }} />
        <Button variant="secondary" size="sm" onClick={saveCreds}>
          {tr("Save")}
        </Button>
        <Button variant="primary" size="sm" onClick={syncNow}>
          {tr("Sync Now")}
        </Button>
      </div>
      {status && <div className="pp-status muted">{status}</div>}
    </div>
  );
}
