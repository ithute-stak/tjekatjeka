"use client";

import { ReactNode, useEffect, useId, useRef, useState } from "react";

type Props = {
  triggerLabel: string;
  title: string;
  description?: string;
  eyebrow?: string;
  size?: "default" | "wide";
  children: ReactNode;
};

export function FormDialog({
  triggerLabel,
  title,
  description,
  eyebrow = "Quick action",
  size = "default",
  children,
}: Props) {
  const [open, setOpen] = useState(false);
  const titleId = useId();
  const descriptionId = useId();
  const closeRef = useRef<HTMLButtonElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    closeRef.current?.focus();

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", onKeyDown);
      triggerRef.current?.focus();
    };
  }, [open]);

  return (
    <>
      <button
        ref={triggerRef}
        type="button"
        className="action-button form-dialog-trigger"
        aria-haspopup="dialog"
        aria-expanded={open}
        onClick={() => setOpen(true)}
      >
        <span aria-hidden>+</span> {triggerLabel}
      </button>

      {open ? (
        <div
          className="form-dialog-backdrop"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) setOpen(false);
          }}
        >
          <section
            className={`form-dialog-panel ${size === "wide" ? "wide" : ""}`}
            role="dialog"
            aria-modal="true"
            aria-labelledby={titleId}
            aria-describedby={description ? descriptionId : undefined}
          >
            <header className="form-dialog-header">
              <div>
                <span className="eyebrow">{eyebrow}</span>
                <h2 id={titleId}>{title}</h2>
                {description ? <p id={descriptionId}>{description}</p> : null}
              </div>
              <button
                ref={closeRef}
                type="button"
                className="form-dialog-close"
                aria-label="Close dialog"
                onClick={() => setOpen(false)}
              >
                ×
              </button>
            </header>
            <div className="form-dialog-body">{children}</div>
          </section>
        </div>
      ) : null}
    </>
  );
}
