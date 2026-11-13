import { renderWithToast as render } from "../test/renderWithToast";
import {
  act,
  cleanup,
  fireEvent,
  screen,
  waitFor,
} from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";
import { ApiError } from "../api/client";
import CompliancePage from "./CompliancePage";
import { noticeFields } from "../types/compliance";

const request = vi.hoisted(() => vi.fn());
vi.mock("../api/client", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../api/client")>()),
  api: request,
  getClinicContext: () => "clinic-a",
}));
afterEach(() => {
  cleanup();
  request.mockReset();
});

test("espera la configuración antes de editar y publica los cambios del usuario", async () => {
  let resolveNotice!: (value: unknown) => void;
  const pending = new Promise((resolve) => {
    resolveNotice = resolve;
  });
  const body = Object.fromEntries(
    noticeFields.map(([key]) => [
      key,
      key === "privacy_email"
        ? "privacy@example.test"
        : "Texto sintético de prueba",
    ]),
  );
  let notice = { id: 1, version: 1, published_at: "2026-01-01", body };
  let initial = true;
  request.mockImplementation((path: string, options?: RequestInit) => {
    if (options?.method === "POST") {
      const payload = JSON.parse(String(options.body));
      notice = { ...notice, version: 2, body: payload };
      return Promise.resolve(notice);
    }
    if (path.includes("consent-templates")) return Promise.resolve([]);
    if (initial) {
      initial = false;
      return pending;
    }
    return Promise.resolve({ notice });
  });
  render(
    <MemoryRouter>
      <CompliancePage />
    </MemoryRouter>,
  );
  expect(
    screen.queryByLabelText("Nombre legal o razón social del responsable"),
  ).toBeNull();
  await act(async () => {
    resolveNotice({ notice });
  });
  fireEvent.change(
    await screen.findByLabelText("Nombre legal o razón social del responsable"),
    { target: { value: "Responsable revisado por el usuario" } },
  );
  fireEvent.click(
    screen.getByLabelText(
      "El responsable revisó estos datos y los procedimientos están disponibles para los titulares.",
    ),
  );
  fireEvent.submit(
    screen
      .getByRole("button", { name: "Publicar nueva versión del aviso" })
      .closest("form")!,
  );
  await waitFor(() =>
    expect(request).toHaveBeenCalledWith(
      "clinics/admin/privacy/",
      expect.objectContaining({
        method: "POST",
        body: expect.stringContaining("Responsable revisado por el usuario"),
      }),
    ),
  );
  expect(await screen.findByText("Aviso versión 2 publicado.")).toBeVisible();
});

test("cada campo tiene una ayuda desplegable que no publica el formulario", async () => {
  request.mockImplementation((path: string) =>
    Promise.resolve(path.includes("consent-templates") ? [] : { notice: null }),
  );
  render(
    <MemoryRouter>
      <CompliancePage />
    </MemoryRouter>,
  );
  const labels = [
    ...noticeFields.map(([, label]) => label),
    "Tipo",
    "Título",
    "Texto completo aprobado",
  ];
  await screen.findByLabelText(labels[0]);
  for (const label of labels) {
    const toggle = screen.getByRole("button", {
      name: `Información sobre ${label}`,
    });
    expect(toggle).toHaveAttribute("type", "button");
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    const panel = document.getElementById(
      toggle.getAttribute("aria-controls")!,
    )!;
    expect(panel).not.toBeVisible();
    fireEvent.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "true");
    expect(panel).toBeVisible();
    expect(panel).toHaveTextContent("Qué agregar:");
    expect(panel).toHaveTextContent("Para qué sirve:");
    expect(screen.getByLabelText(label)).toHaveAttribute(
      "aria-describedby",
      panel.id,
    );
    fireEvent.click(toggle);
    expect(panel).not.toBeVisible();
  }
  expect(request).toHaveBeenCalledTimes(2);
});

test("indica cómo completar el nombre sin perder el aviso y permite reintentar", async () => {
  const body = Object.fromEntries(
    noticeFields.map(([key]) => [
      key,
      key === "privacy_email" ? "privacy@example.test" : "Contenido revisado",
    ]),
  );
  let fail = true;
  request.mockImplementation((path: string, options?: RequestInit) => {
    if (options?.method === "POST") {
      if (fail)
        return Promise.reject(
          new ApiError(
            "El responsable que publica debe tener nombre completo registrado.",
            400,
            {
              detail:
                "El responsable que publica debe tener nombre completo registrado.",
              code: "profile_name_required",
            },
          ),
        );
      return Promise.resolve({ id: 1, version: 1, body });
    }
    return Promise.resolve(
      path.includes("consent-templates")
        ? []
        : { notice: { id: 1, version: 1, body } },
    );
  });
  render(
    <MemoryRouter>
      <CompliancePage />
    </MemoryRouter>,
  );
  const input = await screen.findByLabelText(noticeFields[0][1]);
  fireEvent.change(input, { target: { value: "Contenido sin perder" } });
  fireEvent.click(
    screen.getByLabelText(
      "El responsable revisó estos datos y los procedimientos están disponibles para los titulares.",
    ),
  );
  fireEvent.submit(
    screen
      .getByRole("button", { name: "Publicar nueva versión del aviso" })
      .closest("form")!,
  );
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "nombre completo registrado",
  );
  const link = screen.getByRole("link", { name: /Completar mi nombre/ });
  expect(link).toHaveAttribute("href", "/security");
  expect(link).toHaveAttribute("target", "_blank");
  expect(input).toHaveValue("Contenido sin perder");
  fail = false;
  fireEvent.submit(
    screen
      .getByRole("button", { name: "Publicar nueva versión del aviso" })
      .closest("form")!,
  );
  expect(await screen.findByText("Aviso versión 1 publicado.")).toBeVisible();
});
