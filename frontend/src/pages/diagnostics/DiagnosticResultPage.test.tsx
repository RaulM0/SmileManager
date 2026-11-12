import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { ApiError } from "../../api/client";
import { ToastProvider } from "../../context/ToastContext";
import { imagesService } from "../../services/images";
import DiagnosticResultPage from "./DiagnosticResultPage";

vi.mock("../../services/images", () => ({
  imagesService: { get: vi.fn(), analyze: vi.fn() },
}));
vi.mock("../../components/images/ProtectedImageViewer", () => ({
  default: () => <div>Visor</div>,
}));
beforeEach(() => vi.clearAllMocks());
afterEach(cleanup);

test("ofrece cargar una nueva imagen del paciente cuando falta el original", async () => {
  vi.mocked(imagesService.get).mockResolvedValue({
    id: 7,
    paciente: 12,
    patient_name: "Paciente",
    tipo_imagen: "RX",
    descripcion: "",
    imagen_url: "",
    resultados_url: null,
    fecha_subida: "2026-01-01",
  });
  vi.mocked(imagesService.analyze).mockRejectedValue(
    new ApiError("La imagen original no está disponible.", 404, {
      code: "source_image_missing",
    }),
  );
  render(
    <QueryClientProvider client={new QueryClient()}>
      <ToastProvider>
        <MemoryRouter initialEntries={["/diagnostics/7"]}>
          <Routes>
            <Route path="/diagnostics/:id" element={<DiagnosticResultPage />} />
          </Routes>
        </MemoryRouter>
      </ToastProvider>
    </QueryClientProvider>,
  );
  const analyze = await screen.findByRole("button", {
    name: "Analizar imagen",
  });
  await waitFor(() => expect(analyze).toBeEnabled());
  fireEvent.click(analyze);
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "La imagen original no está disponible.",
  );
  expect(
    await screen.findByRole("link", { name: "Cargar imagen en el expediente" }),
  ).toHaveAttribute("href", "/patients/12/images/upload");
});

test("consultar un resultado no ejecuta el análisis; repetirlo requiere una acción", async () => {
  const image = {
    id: 7,
    paciente: 12,
    patient_name: "Paciente",
    tipo_imagen: "RX",
    descripcion: "",
    imagen_url: "",
    resultados_url: "/resultado.jpg",
    fecha_subida: "2026-01-01",
  };
  vi.mocked(imagesService.get).mockResolvedValue(image);
  vi.mocked(imagesService.analyze).mockResolvedValue({ image, detections: [] });
  render(
    <QueryClientProvider client={new QueryClient()}>
      <ToastProvider>
        <MemoryRouter initialEntries={["/diagnostics/7"]}>
          <Routes>
            <Route path="/diagnostics/:id" element={<DiagnosticResultPage />} />
          </Routes>
        </MemoryRouter>
      </ToastProvider>
    </QueryClientProvider>,
  );
  const rerun = await screen.findByRole("button", {
    name: "Analizar nuevamente",
  });
  expect(imagesService.analyze).not.toHaveBeenCalled();
  fireEvent.click(rerun);
  expect(imagesService.analyze).toHaveBeenCalledTimes(1);
});
