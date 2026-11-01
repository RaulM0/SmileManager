import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen } from "@testing-library/react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { expect, test, vi } from "vitest";
import { ToastProvider } from "../../context/ToastContext";
import { clinicalService } from "../../services/clinical";
import ConsultationCreatePage from "./ConsultationCreatePage";

vi.mock("../../hooks/useResource", () => ({ useResource: () => ({ data: { nombre: "ANA", appat: "LOPEZ" }, error: null, reload: vi.fn() }) }));
vi.mock("../../services/clinical", () => ({ clinicalService: { createConsultation: vi.fn() } }));

test("tras registrar la consulta requerida vuelve a cargar la imagen del mismo paciente", async () => {
  vi.mocked(clinicalService.createConsultation).mockResolvedValue({ id: 5, paciente: { id: 7, nombre: "ANA", appat: "LOPEZ", apmat: "", full_name: "ANA LOPEZ", estatus: "A" }, fecha_consulta: "2026-01-01", motivo_consulta: "CONTROL", diagnostico: "", tratamiento: "", observaciones: "" });
  const router = createMemoryRouter([
    { path: "/patients/:id/consultations/new", element: <ConsultationCreatePage /> },
    { path: "/patients/:id/images/upload", element: <h1>Cargar imagen clínica</h1> },
  ], { initialEntries: ["/patients/7/consultations/new?continue=images"] });
  render(<QueryClientProvider client={new QueryClient()}><ToastProvider><RouterProvider router={router} /></ToastProvider></QueryClientProvider>);
  fireEvent.change(screen.getByLabelText("Motivo de consulta"), { target: { value: "CONTROL" } });
  fireEvent.click(screen.getByRole("button", { name: "Registrar consulta" }));
  expect(await screen.findByRole("heading", { name: "Cargar imagen clínica" }, { timeout: 10000 })).toBeInTheDocument();
  expect(clinicalService.createConsultation).toHaveBeenCalledWith("7", expect.objectContaining({ motivo_consulta: "CONTROL" }));
}, 15000);
