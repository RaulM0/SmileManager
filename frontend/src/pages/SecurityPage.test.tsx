import { renderWithToast as render } from "../test/renderWithToast";
import { cleanup, fireEvent, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";
import { api } from "../api/client";
import SecurityPage from "./SecurityPage";

vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({
    user: { first_name: "Persona", last_name: "Sintética", mfa_enabled: true },
    logout: vi.fn(),
  }),
}));
vi.mock("../api/client", () => ({
  api: vi.fn(),
  getErrorMessage: (reason: Error) => reason.message,
}));
afterEach(() => {
  cleanup();
  vi.resetAllMocks();
});

test("guardar el nombre muestra un toast de éxito y los errores usan el toast de error", async () => {
  vi.mocked(api)
    .mockResolvedValueOnce([])
    .mockResolvedValueOnce({})
    .mockRejectedValueOnce(new Error("No fue posible guardar."));
  render(
    <MemoryRouter>
      <SecurityPage />
    </MemoryRouter>,
  );
  fireEvent.click(screen.getByRole("button", { name: "Guardar nombre" }));
  expect(await screen.findByRole("status")).toHaveClass("is-success");
  expect(screen.getByRole("status")).toHaveTextContent("Nombre actualizado");
  fireEvent.click(screen.getByRole("button", { name: "Guardar nombre" }));
  expect(await screen.findByRole("alert")).toHaveClass("is-error");
  expect(screen.getByRole("alert")).toHaveTextContent(
    "No fue posible guardar.",
  );
});
