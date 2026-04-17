import { useEffect, type ReactNode } from "react";
import { Modal } from "./Modal";
import { Button } from "./Button";
import "./ConfirmDialog.scss";

interface Props {
  open: boolean;
  title: string;
  body?: ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  danger?: boolean;
  onConfirm: () => void;
  onClose: () => void;
}

export function ConfirmDialog({
  open,
  title,
  body,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  danger = false,
  onConfirm,
  onClose,
}: Props) {
  useEffect(() => {
    if (!open) return;
    // Autofocus the confirm button once the modal renders.
    const el = document.querySelector<HTMLButtonElement>(
      ".confirm-dialog-confirm",
    );
    el?.focus();
    const h = (e: KeyboardEvent) => {
      if (e.key === "Enter") {
        e.preventDefault();
        onConfirm();
      }
    };
    window.addEventListener("keydown", h);
    return () => window.removeEventListener("keydown", h);
  }, [open, onConfirm]);

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={title}
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>
            {cancelLabel}
          </Button>
          <Button
            variant={danger ? "danger" : "primary"}
            onClick={onConfirm}
            className={
              danger
                ? "confirm-dialog-confirm confirm-dialog-confirm--danger"
                : "confirm-dialog-confirm"
            }
          >
            {confirmLabel}
          </Button>
        </>
      }
    >
      {body && <div className="confirm-dialog-body">{body}</div>}
    </Modal>
  );
}
