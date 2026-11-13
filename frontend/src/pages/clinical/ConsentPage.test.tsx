import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";
import ConsentPage from "./ConsentPage";

const service = vi.hoisted(() => ({ consent: vi.fn(), saveConsent: vi.fn() }));
vi.mock("../../services/clinical", () => ({ clinicalService: service }));
vi.mock("../../context/ToastContext", () => ({
  useToast: () => ({ success: vi.fn() }),
}));
vi.mock("../../hooks/useUnsavedChanges", () => ({
  useUnsavedChanges: () => ({ markSaved: vi.fn(), prompt: null }),
}));
vi.mock("../../hooks/useApiDownload", () => ({
  useApiDownload: () => ({ active: null, download: vi.fn() }),
}));
afterEach(() => {
  cleanup();
  service.consent.mockReset();
  service.saveConsent.mockReset();
});
function mount() {
  render(
    <MemoryRouter initialEntries={["/patients/7/consent"]}>
      <Routes>
        <Route path="/patients/:id/consent" element={<ConsentPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

test("sin plantilla aprobada no permite registrar aceptación ni identificación", async () => {
  service.consent.mockResolvedValue({
    templates: [],
    records: [],
    legacy: {
      texto: "Texto histórico",
      fecha_aceptacion: "2025-01-01",
      pdf_generado: null,
      archivo_ine_url: null,
    },
  });
  mount();
  expect(
    await screen.findByText("Registro pendiente de configuración"),
  ).toBeVisible();
  expect(
    screen.getByText("Registro histórico sin firma verificada"),
  ).toBeVisible();
  expect(
    screen.queryByRole("button", { name: "Registrar evidencia" }),
  ).toBeNull();
});

test("envía plantilla, identidad y documento firmado sin reutilizar el flujo de INE", async () => {
  service.consent.mockResolvedValue({
    templates: [
      {
        id: 3,
        kind: "CLINICAL",
        version: 1,
        title: "Texto aprobado",
        text: "Texto sintético de prueba",
      },
    ],
    records: [],
    legacy: null,
  });
  service.saveConsent.mockResolvedValue({ id: 1 });
  mount();
  await screen.findByText("Registrar documento firmado");
  fireEvent.change(screen.getByLabelText("Nombre completo del firmante"), {
    target: { value: "Paciente Sintético" },
  });
  fireEvent.change(screen.getByLabelText("Fecha de firma"), {
    target: { value: "2026-01-01" },
  });
  fireEvent.change(screen.getByLabelText("Documento firmado completo"), {
    target: {
      files: [
        new File(["synthetic"], "signed.pdf", { type: "application/pdf" }),
      ],
    },
  });
  fireEvent.click(screen.getByRole("checkbox"));
  fireEvent.submit(
    screen
      .getByRole("button", { name: "Registrar evidencia" })
      .closest("form")!,
  );
  await waitFor(() => expect(service.saveConsent).toHaveBeenCalled());
  const data = service.saveConsent.mock.calls[0][1] as FormData;
  expect(data.get("template_id")).toBe("3");
  expect(data.get("signer_name")).toBe("Paciente Sintético");
  expect(data.get("signed_document")).toBeInstanceOf(File);
  expect(data.has("archivo_ine")).toBe(false);
  expect(data.has("texto")).toBe(false);
});

test("bloquea la descarga de evidencia pendiente y explica la cuarentena", async () => {
  service.consent.mockResolvedValue({
    templates: [],
    legacy: null,
    records: [
      {
        id: 9,
        template: { kind: "CLINICAL", version: 1 },
        signer_name: "Persona sintética",
        signed_on: "2026-01-01",
        recorded_name: "Operador sintético",
        recorded_at: "2026-01-01T12:00:00Z",
        integrity: "verified",
        revoked_at: null,
        superseded: false,
        scan_status: "PENDING",
      },
    ],
  });
  mount();
  expect(
    await screen.findByRole("button", { name: "Descargar documento #9" }),
  ).toBeDisabled();
  expect(screen.getByText(/Documento en cuarentena/)).toBeVisible();
});
