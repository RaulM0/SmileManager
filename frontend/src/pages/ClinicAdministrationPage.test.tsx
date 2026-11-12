import { renderWithToast as render } from "../test/renderWithToast";
import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { afterEach, expect, it, vi } from "vitest";
import ClinicAdministrationPage from "./ClinicAdministrationPage";
import { MemoryRouter } from "react-router-dom";

const request = vi.hoisted(() => vi.fn());
vi.mock("../api/client", () => ({
  api: request,
  getClinicContext: () => "clinic-a",
  getErrorMessage: (error: Error) => error.message,
}));
afterEach(() => {
  cleanup();
  request.mockReset();
});

it("creates an invitation using a clinic role and displays only the returned clinic data", async () => {
  request.mockImplementation((path: string, options?: RequestInit) => {
    if (options?.method === "POST")
      return Promise.resolve({ detail: "Enviada" });
    if (path.includes("dashboard"))
      return Promise.resolve({
        patients: { active: 2 },
        appointments: { today: 1, pending: 1 },
        members: { doctors: 1, staff: 0 },
        ai: { total: 0, failed: 0 },
      });
    return Promise.resolve({
      count: 0,
      next: null,
      previous: null,
      results: [],
    });
  });
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  render(
    <MemoryRouter>
      <QueryClientProvider client={client}>
        <ClinicAdministrationPage />
      </QueryClientProvider>
    </MemoryRouter>,
  );
  expect(await screen.findByText("Pacientes activos")).toBeTruthy();
  fireEvent.change(screen.getByLabelText("Correo electrónico"), {
    target: { value: "doctor@example.test" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Enviar invitación" }));
  await waitFor(() =>
    expect(request).toHaveBeenCalledWith(
      "clinics/invitations/",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ email: "doctor@example.test", role: "DOCTOR" }),
      }),
    ),
  );
  expect(screen.queryByRole("option", { name: /platform/i })).toBeNull();
  client.clear();
});

it("does not offer direct reactivation for a revoked membership", async () => {
  request.mockImplementation((path: string) => {
    if (path.includes("dashboard"))
      return Promise.resolve({
        patients: { active: 0 },
        appointments: { today: 0, pending: 0 },
        members: { doctors: 0, staff: 0 },
        ai: { total: 0, failed: 0 },
      });
    if (path.includes("memberships"))
      return Promise.resolve({
        count: 1,
        next: null,
        previous: null,
        results: [
          {
            id: "member",
            username: "doctor",
            email: "doctor@example.test",
            role: "DOCTOR",
            status: "REVOKED",
          },
        ],
      });
    return Promise.resolve({
      count: 0,
      next: null,
      previous: null,
      results: [],
    });
  });
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  render(
    <MemoryRouter>
      <QueryClientProvider client={client}>
        <ClinicAdministrationPage />
      </QueryClientProvider>
    </MemoryRouter>,
  );
  expect(await screen.findByText("Requiere una nueva invitación")).toBeTruthy();
  expect(screen.queryByRole("button", { name: "Reactivar" })).toBeNull();
  expect(screen.getByLabelText("Rol de doctor")).toBeDisabled();
  client.clear();
});
