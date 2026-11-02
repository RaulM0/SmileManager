import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { useState } from "react";
import { createMemoryRouter, Link, RouterProvider } from "react-router-dom";
import { afterEach, expect, test } from "vitest";
import { discardDraftsFor, hasUnsavedChanges, useUnsavedChanges } from "./useUnsavedChanges";
afterEach(cleanup);

function Draft() {
  const [value, setValue] = useState("");
  const guard = useUnsavedChanges(value !== "");
  return <><label htmlFor="draft">Borrador</label><input id="draft" value={value} onChange={(event) => setValue(event.target.value)} /><Link to="/other">Salir</Link>{guard.prompt}</>;
}

test("protege el borrador y permite seguir editando o descartar", async () => {
  Object.defineProperty(HTMLDialogElement.prototype, "showModal", { configurable: true, value: function (this: HTMLDialogElement) { this.setAttribute("open", ""); } });
  Object.defineProperty(HTMLDialogElement.prototype, "close", { configurable: true, value: function (this: HTMLDialogElement) { this.removeAttribute("open"); } });
  const router = createMemoryRouter([{ path: "/", element: <Draft /> }, { path: "/other", element: <h1>Destino</h1> }], { initialEntries: ["/"] });
  render(<RouterProvider router={router} />);
  fireEvent.change(screen.getByLabelText("Borrador"), { target: { value: "dato" } });
  fireEvent.click(screen.getByRole("link", { name: "Salir" }));
  let dialog = await screen.findByRole("dialog", { name: "Cambios sin guardar" });
  fireEvent.click(within(dialog).getByRole("button", { name: "Volver" }));
  expect(screen.getByLabelText("Borrador")).toHaveValue("dato");
  fireEvent.click(screen.getByRole("link", { name: "Salir" }));
  dialog = await screen.findByRole("dialog", { name: "Cambios sin guardar" });
  fireEvent.click(within(dialog).getByRole("button", { name: "Descartar cambios" }));
  await waitFor(() => expect(screen.getByRole("heading", { name: "Destino" })).toBeInTheDocument());
});

test("no bloquea la navegación cuando no hay cambios", async () => {
  const router = createMemoryRouter([{ path: "/", element: <Draft /> }, { path: "/other", element: <h1>Destino</h1> }], { initialEntries: ["/"] });
  render(<RouterProvider router={router} />);
  fireEvent.click(screen.getByRole("link", { name: "Salir" }));
  await waitFor(() => expect(screen.getByRole("heading", { name: "Destino" })).toBeInTheDocument());
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
});

test("restaura la protección si falla el cierre de sesión", async () => {
  const router = createMemoryRouter([{ path: "/", element: <Draft /> }], { initialEntries: ["/"] });
  render(<RouterProvider router={router} />);
  fireEvent.change(screen.getByLabelText("Borrador"), { target: { value: "dato" } });
  await waitFor(() => expect(hasUnsavedChanges()).toBe(true));
  await expect(discardDraftsFor(async () => { throw new Error("Sin conexión"); })).rejects.toThrow("Sin conexión");
  expect(hasUnsavedChanges()).toBe(true);
});
