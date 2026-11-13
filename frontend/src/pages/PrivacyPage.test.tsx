import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";
import PrivacyPage from "./PrivacyPage";

const request = vi.hoisted(() => vi.fn());
vi.mock("../api/client", () => ({
  api: request,
  getErrorMessage: (error: Error) => error.message,
}));
afterEach(() => {
  cleanup();
  request.mockReset();
});

test("no publica un aviso genérico cuando falta configuración del responsable", async () => {
  request.mockResolvedValue({ configured: false, notice: null });
  render(
    <MemoryRouter>
      <PrivacyPage />
    </MemoryRouter>,
  );
  expect(
    await screen.findByText("Aviso pendiente de configuración"),
  ).toBeVisible();
  expect(screen.queryByText(/SmileManager, responsable/)).toBeNull();
});

test("el aviso público presenta únicamente la versión y datos publicados por la clínica", async () => {
  request.mockResolvedValue({
    configured: true,
    notice: {
      id: 1,
      version: 2,
      published_at: "2026-01-01T12:00:00Z",
      body: {
        legal_name: "Responsable Sintético",
        address: "Domicilio sintético",
        privacy_email: "privacy@example.test",
      },
    },
  });
  render(
    <MemoryRouter initialEntries={["/privacy/clinic-test"]}>
      <Routes>
        <Route path="/privacy/:clinicSlug" element={<PrivacyPage />} />
      </Routes>
    </MemoryRouter>,
  );
  expect(await screen.findByText("Responsable Sintético")).toBeVisible();
  expect(screen.getByText("Domicilio sintético")).toBeVisible();
  expect(request).toHaveBeenCalledWith("privacy/clinic-test/");
});
