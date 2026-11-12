import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";
import { ToastProvider } from "../../context/ToastContext";
import { clinicalService } from "../../services/clinical";
import OdontogramPage from "./OdontogramPage";
import { ApiError } from "../../api/client";

vi.mock("../../services/clinical", () => ({
  clinicalService: { odontogram: vi.fn(), saveOdontogram: vi.fn() },
}));
afterEach(cleanup);

test("un odontograma sin registro no afirma salud y guarda solo superficies documentadas", async () => {
  vi.mocked(clinicalService.odontogram).mockResolvedValue({
    denticion_permanente: {},
    denticion_decidua: {},
  });
  vi.mocked(clinicalService.saveOdontogram).mockResolvedValue({
    denticion_permanente: {},
    denticion_decidua: {},
  });
  const router = createMemoryRouter(
    [{ path: "/patients/:id/odontogram", element: <OdontogramPage /> }],
    { initialEntries: ["/patients/1/odontogram"] },
  );
  render(
    <ToastProvider>
      <RouterProvider router={router} />
    </ToastProvider>,
  );
  await screen.findByRole("heading", { name: "Odontograma" });
  const surface = document.querySelector<HTMLButtonElement>(
    'button[aria-label="18 oclusal sin registrar"]',
  );
  expect(surface).not.toBeNull();
  const summary = screen.getByLabelText("Resumen del odontograma");
  expect(
    within(summary).getByText("Sanos").nextElementSibling,
  ).toHaveTextContent("0");
  fireEvent.click(screen.getByRole("button", { name: "Caries" }));
  fireEvent.click(surface!);
  fireEvent.click(screen.getByRole("button", { name: "Guardar odontograma" }));
  await waitFor(() =>
    expect(clinicalService.saveOdontogram).toHaveBeenCalled(),
  );
  const saved = vi.mocked(clinicalService.saveOdontogram).mock.calls[0][1];
  expect(saved.denticion_permanente).toEqual({ "18": { oclusal: "caries" } });
  expect(saved.denticion_decidua).toEqual({});
}, 15000);

test("avisa cuando el odontograma cambió en otra sesión", async () => {
  vi.mocked(clinicalService.odontogram).mockResolvedValue({
    version: 3,
    denticion_permanente: {},
    denticion_decidua: {},
  });
  vi.mocked(clinicalService.saveOdontogram).mockRejectedValue(
    new ApiError(
      "Este expediente fue actualizado desde otra sesión. Recarga la información antes de guardar tus cambios.",
      409,
      null,
    ),
  );
  const router = createMemoryRouter(
    [{ path: "/patients/:id/odontogram", element: <OdontogramPage /> }],
    { initialEntries: ["/patients/1/odontogram"] },
  );
  render(
    <ToastProvider>
      <RouterProvider router={router} />
    </ToastProvider>,
  );
  await screen.findByRole("heading", { name: "Odontograma" });
  fireEvent.click(screen.getByRole("button", { name: "Guardar odontograma" }));
  await screen.findByText(/actualizado desde otra sesión/i);
});
