import { useEffect, useState } from "react";
import { Modal } from "../primitives/Modal";
import { Button } from "../primitives/Button";
import { Field, TextInput } from "../primitives/Field";
import { ConfirmDialog } from "../primitives/ConfirmDialog";
import { addSubject, deleteSubject, renameSubject } from "@/lib/ipc";
import { tr } from "@/lib/i18n";

interface Props {
  open: boolean;
  onClose: () => void;
  editing?: string | null;
}

export function AddSubjectDialog({ open, onClose, editing }: Props) {
  const [name, setName] = useState("");
  const [confirmOpen, setConfirmOpen] = useState(false);
  useEffect(() => {
    if (open) setName(editing ?? "");
  }, [open, editing]);

  async function save() {
    const v = name.trim();
    if (!v) return;
    try {
      if (editing) await renameSubject(editing, v);
      else await addSubject(v);
      onClose();
    } catch (e) {
      console.error(e);
    }
  }

  function remove() {
    if (!editing) return;
    setConfirmOpen(true);
  }

  async function confirmRemove() {
    if (!editing) return;
    await deleteSubject(editing);
    setConfirmOpen(false);
    onClose();
  }

  return (
    <>
      <Modal
        open={open}
        onClose={onClose}
        title={editing ? tr("Edit subject") : tr("New subject")}
        footer={
          <>
            {editing && (
              <Button variant="danger" onClick={remove}>
                {tr("Delete")}
              </Button>
            )}
            <div style={{ flex: 1 }} />
            <Button variant="ghost" onClick={onClose}>
              {tr("Cancel")}
            </Button>
            <Button variant="primary" onClick={save}>
              {tr("Save")}
            </Button>
          </>
        }
      >
        <Field label={tr("Subject")}>
          <TextInput
            autoFocus
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </Field>
      </Modal>
      <ConfirmDialog
        open={confirmOpen}
        title={editing ? `${tr("Delete")} ${editing}?` : tr("Delete")}
        confirmLabel={tr("Delete")}
        cancelLabel={tr("Cancel")}
        danger
        onConfirm={confirmRemove}
        onClose={() => setConfirmOpen(false)}
      />
    </>
  );
}
