import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";
import { ToastProvider } from "../../context/ToastContext";
import { appointmentsService } from "../../services/appointments";
import AppointmentsPage from "./AppointmentsPage";

vi.mock("../../services/appointments", () => ({
  appointmentsService: { list: vi.fn(), range: vi.fn(), transition: vi.fn() },
}));
afterEach(() => vi.restoreAllMocks());

test("cancelar exige confirmar la cita y permite volver sin enviar cambios", async () => {
  Object.defineProperty(HTMLDialogElement.prototype, "showModal", {
    configurable: true,
    value: function (this: HTMLDialogElement) {
      this.setAttribute("open", "");
    },
  });
  Object.defineProperty(HTMLDialogElement.prototype, "close", {
    configurable: true,
    value: function (this: HTMLDialogElement) {
      this.removeAttribute("open");
    },
  });
  const appointment = {
    id: 7,
    fecha: "2026-10-24",
    hora: "10:00:00",
    estatus: "P" as const,
    motivo: "Control",
    observaciones: "",
    paciente: {
      id: 1,
      nombre: "ANA",
      appat: "LOPEZ",
      apmat: "",
      full_name: "ANA LOPEZ",
      estatus: "A" as const,
    },
  };
  vi.mocked(appointmentsService.list).mockResolvedValue({
    count: 1,
    next: null,
    previous: null,
    results: [appointment],
  });
  vi.mocked(appointmentsService.range).mockResolvedValue([appointment]);
  vi.mocked(appointmentsService.transition).mockResolvedValue({
    ...appointment,
    estatus: "A",
  });
  render(
    <QueryClientProvider
      client={
        new QueryClient({ defaultOptions: { queries: { retry: false } } })
      }
    >
      <ToastProvider>
        <MemoryRouter>
          <AppointmentsPage />
        </MemoryRouter>
      </ToastProvider>
    </QueryClientProvider>,
  );
  fireEvent.click(
    await screen.findByRole("button", { name: "Cancelar" }, { timeout: 10000 }),
  );
  let dialog = screen.getByRole("dialog", { name: "Cancelar cita" });
  expect(dialog).toHaveTextContent("ANA LOPEZ");
  expect(appointmentsService.transition).not.toHaveBeenCalled();
  fireEvent.click(within(dialog).getByRole("button", { name: "Volver" }));
  expect(appointmentsService.transition).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));
  dialog = screen.getByRole("dialog", { name: "Cancelar cita" });
  fireEvent.click(
    within(dialog).getByRole("button", { name: "Sí, cancelar cita" }),
  );
  await waitFor(() =>
    expect(appointmentsService.transition).toHaveBeenCalledWith(7, "cancel"),
  );
}, 20000);
