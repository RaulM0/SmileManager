import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { ToastProvider, useToast } from "./ToastContext";

afterEach(() => { cleanup(); vi.useRealTimers(); });

function ActionFixture() {
  const toast = useToast();
  return <>
    <button onClick={() => toast.error("No se pudo guardar")}>Error</button>
    <button onClick={() => toast.warning("Revisa los datos antes de continuar")}>Advertencia</button>
    <button onClick={() => toast.success("Guardado correctamente")}>Éxito</button>
  </>;
}

test("el éxito reemplaza un error anterior y puede cerrarse", () => {
  render(<ToastProvider><ActionFixture /></ToastProvider>);
  fireEvent.click(screen.getByRole("button", { name: "Error" }));
  expect(screen.getByRole("alert")).toHaveTextContent("No se pudo guardar");
  fireEvent.click(screen.getByRole("button", { name: "Éxito" }));
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  expect(screen.getByRole("status")).toHaveTextContent("Guardado correctamente");
  fireEvent.click(screen.getByRole("button", { name: "Cerrar notificación" }));
  expect(screen.queryByRole("status")).not.toBeInTheDocument();
});


test("las advertencias se muestran como toast y se cierran automáticamente", () => {
  vi.useFakeTimers();
  render(<ToastProvider><ActionFixture /></ToastProvider>);
  fireEvent.click(screen.getByRole('button', { name: 'Advertencia' }));
  expect(screen.getByRole('alert')).toHaveClass('is-warning');
  expect(screen.getByRole('alert')).toHaveTextContent('Revisa los datos antes de continuar');
  act(() => vi.advanceTimersByTime(8000));
  expect(screen.queryByRole('alert')).not.toBeInTheDocument();
});

test("el toast permanece visible dentro de la capa de un diálogo abierto", async () => {
  render(<ToastProvider><dialog open><ActionFixture /></dialog></ToastProvider>);
  fireEvent.click(screen.getByRole('button', { name: 'Error' }));
  await waitFor(() => expect(screen.getByRole('alert').closest('dialog')).not.toBeNull());
});
