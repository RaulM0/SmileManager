import { useRef, useState } from "react";
import { downloadApiFile, getErrorMessage } from "../api/client";
import { useToast } from "../context/ToastContext";

/** Keeps download feedback and duplicate-click handling consistent. */
export function useApiDownload() {
  const [active, setActive] = useState<string | null>(null);
  const busy = useRef(false);
  const toast = useToast();
  async function download(key: string, path: string, filename: string) {
    if (busy.current) return;
    busy.current = true;
    setActive(key);
    try { await downloadApiFile(path, filename); toast.success("Descarga iniciada."); }
    catch (error) { toast.error(getErrorMessage(error)); }
    finally { busy.current = false; setActive(null); }
  }
  return { active, download };
}
