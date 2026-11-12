import { renderWithToast as render } from "../test/renderWithToast";
import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { afterEach, expect, it, vi } from "vitest";
import StaffAgendaPage from "./StaffAgendaPage";

const request = vi.hoisted(() => vi.fn());
vi.mock("../api/client", () => ({ api: request, getClinicContext: () => "clinic-a", getErrorMessage: (error: Error) => error.message }));
afterEach(() => { cleanup(); request.mockReset(); });

it("creates reception appointments without exposing an expediente or diagnosis", async () => {
  request.mockImplementation((path: string, options?: RequestInit) => {
    if (options?.method === "POST") return Promise.resolve({ id: 7 });
    if (path.includes("/patients/")) return Promise.resolve({ results: [{ id: 5, name: "Paciente Demo", doctor: "Médico Demo" }] });
    return Promise.resolve({ count: 0, results: [], next: null, previous: null });
  });
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const router = createMemoryRouter([{ path: "/", element: <QueryClientProvider client={client}><StaffAgendaPage /></QueryClientProvider> }]);
  render(<RouterProvider router={router} />);
  await screen.findByRole("option", { name: "Paciente Demo · Médico Demo" });
  fireEvent.change(screen.getByLabelText("Paciente"), { target: { value: "5" } });
  fireEvent.change(screen.getByLabelText("Fecha"), { target: { value: "2030-01-15" } });
  fireEvent.change(screen.getByLabelText("Motivo de la cita"), { target: { value: "Control" } });
  fireEvent.click(screen.getByRole("button", { name: "Guardar cita" }));
  await waitFor(() => expect(request).toHaveBeenCalledWith("clinics/staff/appointments/", expect.objectContaining({ method: "POST", body: JSON.stringify({ paciente_id: 5, fecha: "2030-01-15", hora: "10:00", motivo: "Control" }) })));
  expect(screen.queryByRole("link", { name: /expediente/i })).toBeNull();
  expect(screen.queryByLabelText(/diagnóstico/i)).toBeNull();
  expect(await screen.findByRole("status")).toHaveTextContent("Cita guardada correctamente.");
  client.clear();
});

it("shows agenda errors without reusing another clinic's data", async () => {
  request.mockRejectedValue(new Error("Acceso revocado"));
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const router = createMemoryRouter([{ path: "/", element: <QueryClientProvider client={client}><StaffAgendaPage /></QueryClientProvider> }]);
  render(<RouterProvider router={router} />);
  expect(await screen.findByText("No fue posible cargar la agenda.")).toHaveAttribute("role", "alert");
  expect(screen.queryByRole("row")).toBeNull();
  client.clear();
});
