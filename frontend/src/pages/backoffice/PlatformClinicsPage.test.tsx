import { renderWithToast as render } from "../../test/renderWithToast";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { api } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import PlatformClinicsPage from "./PlatformClinicsPage";

vi.mock("../../api/client", () => ({
  api: vi.fn(),
  getErrorMessage: (error: Error) => error.message,
}));
vi.mock("../../context/AuthContext", () => ({ useAuth: vi.fn() }));
afterEach(() => {
  cleanup();
  vi.resetAllMocks();
});

function show(isPlatformAdmin: boolean) {
  vi.mocked(useAuth).mockReturnValue({
    user: { id: 1, username: "test", is_platform_admin: isPlatformAdmin },
  } as ReturnType<typeof useAuth>);
  return render(
    <QueryClientProvider
      client={
        new QueryClient({ defaultOptions: { queries: { retry: false } } })
      }
    >
      <PlatformClinicsPage />
    </QueryClientProvider>,
  );
}

it("does not request platform data for another administrator", () => {
  show(false);
  expect(screen.getByRole("alert")).toHaveTextContent("No tienes permiso");
  expect(api).not.toHaveBeenCalled();
});

it("creates an inactive clinic and requests an initial administrator invitation", async () => {
  vi.mocked(api).mockImplementation((path, options) =>
    options?.method === "POST"
      ? Promise.resolve({})
      : Promise.resolve({ count: 0, next: null, previous: null, results: [] }),
  );
  show(true);
  fireEvent.change(screen.getByLabelText("Nombre"), {
    target: { value: "Clínica Sintética" },
  });
  fireEvent.change(screen.getByLabelText("Identificador"), {
    target: { value: "clinica-sintetica" },
  });
  fireEvent.change(screen.getByLabelText("Correo del administrador inicial"), {
    target: { value: "admin@example.test" },
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Crear y enviar invitación" }),
  );
  await waitFor(() =>
    expect(api).toHaveBeenCalledWith(
      "backoffice/clinics/",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          name: "Clínica Sintética",
          slug: "clinica-sintetica",
          status: "INACTIVE",
          initial_admin_email: "admin@example.test",
        }),
      }),
    ),
  );
});
