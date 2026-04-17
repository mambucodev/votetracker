import type { InputHTMLAttributes, SelectHTMLAttributes, ReactNode } from "react";
import "./Field.scss";

export function Field({
  label,
  children,
  hint,
}: {
  label: string;
  children: ReactNode;
  hint?: string;
}) {
  return (
    <label className="field">
      <span className="field-label">{label}</span>
      {children}
      {hint && <span className="field-hint">{hint}</span>}
    </label>
  );
}

export function TextInput(props: InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className={`input ${props.className ?? ""}`} />;
}

export function NumberInput(props: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      type="number"
      {...props}
      className={`input ${props.className ?? ""}`}
    />
  );
}

export function Select(
  props: SelectHTMLAttributes<HTMLSelectElement> & { children: ReactNode },
) {
  return (
    <select {...props} className={`input ${props.className ?? ""}`}>
      {props.children}
    </select>
  );
}
