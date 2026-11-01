import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import { ToastProvider, useToast } from "./ToastContext";

function ActionFixture() {
  const toast = useToast();
  return <>
    <button onClick={() => toast.error("No se pudo guardar")}>Error</button>
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
