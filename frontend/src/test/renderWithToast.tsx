import type { ReactElement } from "react";
import { render } from "@testing-library/react";
import { ToastProvider } from "../context/ToastContext";

export function renderWithToast(element: ReactElement) {
  return render(<ToastProvider>{element}</ToastProvider>);
}
