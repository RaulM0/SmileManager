import { useEffect, useRef } from "react";
import { useBlocker } from "react-router-dom";
import { ConfirmDialog } from "../components/ConfirmDialog";

const drafts = new Set<{ current: boolean }>();
export function hasUnsavedChanges() { return Array.from(drafts).some((draft) => draft.current); }

/** Temporarily releases navigation after an explicit discard; restore on failure. */
export async function discardDraftsFor<T>(action: () => Promise<T>): Promise<T> {
  const active = Array.from(drafts).filter((draft) => draft.current);
  active.forEach((draft) => { draft.current = false; });
  try { return await action(); }
  catch (error) { active.forEach((draft) => { draft.current = true; }); throw error; }
}

/** Blocks navigation only while a draft differs from its saved baseline. */
export function useUnsavedChanges(dirty: boolean) {
  const dirtyRef = useRef(dirty);
  useEffect(() => { drafts.add(dirtyRef); return () => { drafts.delete(dirtyRef); }; }, []);
  useEffect(() => { dirtyRef.current = dirty; }, [dirty]);
  const blocker = useBlocker(() => dirtyRef.current);
  useEffect(() => {
    const warn = (event: BeforeUnloadEvent) => {
      if (dirtyRef.current) { event.preventDefault(); event.returnValue = ""; }
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, []);
  const prompt = blocker.state === "blocked" ? <ConfirmDialog title="Cambios sin guardar" confirmLabel="Descartar cambios" busy={false}
    onClose={() => blocker.reset()} onConfirm={() => blocker.proceed()}>
    <p>Si sales ahora, perderás los cambios que todavía no has guardado.</p>
  </ConfirmDialog> : null;
  return { prompt, markSaved: () => { dirtyRef.current = false; } };
}
