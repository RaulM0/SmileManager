import { renderWithToast as render } from "../test/renderWithToast";
import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";
import { api, ApiError } from "../api/client";
import { ForgotPasswordPage, ResetPasswordPage } from "./PasswordRecovery";

vi.mock("../api/client", () => ({
  api: vi.fn(),
  ApiError: class extends Error {
    status: number;
    payload: Record<string, unknown> | null;
    constructor(
      message: string,
      status: number,
      payload: Record<string, unknown> | null,
    ) {
      super(message);
      this.status = status;
      this.payload = payload;
    }
  },
}));
afterEach(() => {
  cleanup();
  vi.resetAllMocks();
  window.history.replaceState(null, "", "/");
});
const show = (element: React.ReactNode) =>
  render(<MemoryRouter>{element}</MemoryRouter>);

test("solicitud muestra respuesta genérica y estado de carga", async () => {
  let finish!: (value: unknown) => void;
  vi.mocked(api).mockReturnValue(
    new Promise((resolve) => {
      finish = resolve;
    }),
  );
  show(<ForgotPasswordPage />);
  fireEvent.change(screen.getByLabelText("Correo electrónico"), {
    target: { value: "synthetic@example.test" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Enviar instrucciones" }));
  expect(screen.getByRole("button", { name: "Enviando…" })).toBeDisabled();
  finish({ message: "ok" });
  expect(
    await screen.findByText(/Si existe una cuenta elegible/),
  ).toBeInTheDocument();
});

test("restablecimiento comprueba coincidencia y muestra éxito", async () => {
  window.history.replaceState(null, "", "/reset-password#uid=MQ&token=sample");
  vi.mocked(api).mockResolvedValue({ message: "ok" });
  show(<ResetPasswordPage />);
  expect(window.location.hash).toBe("");
  fireEvent.change(screen.getByLabelText("Nueva contraseña"), {
    target: { value: "new passphrase" },
  });
  fireEvent.change(screen.getByLabelText("Confirmar contraseña"), {
    target: { value: "different" },
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Restablecer contraseña" }),
  );
  expect(screen.getByRole("alert")).toHaveTextContent("no coinciden");
  expect(api).not.toHaveBeenCalled();
  fireEvent.change(screen.getByLabelText("Confirmar contraseña"), {
    target: { value: "new passphrase" },
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Restablecer contraseña" }),
  );
  await waitFor(() => expect(api).toHaveBeenCalledTimes(2));
  expect(
    await screen.findByText("Tu contraseña se actualizó correctamente."),
  ).toBeInTheDocument();
  expect(screen.getByRole("link", { name: "Iniciar sesión" })).toHaveAttribute(
    "href",
    "/login",
  );
});

test("enlace inválido y contraseña débil se muestran sin detalles internos", async () => {
  window.history.replaceState(null, "", "/reset-password#uid=MQ&token=sample");
  vi.mocked(api)
    .mockRejectedValueOnce(
      new ApiError("error", 400, {
        new_password: ["Contraseña demasiado común."],
      }),
    )
    .mockRejectedValueOnce(
      new ApiError("error", 400, { code: "invalid_reset" }),
    );
  show(<ResetPasswordPage />);
  fireEvent.change(screen.getByLabelText("Nueva contraseña"), {
    target: { value: "password" },
  });
  fireEvent.change(screen.getByLabelText("Confirmar contraseña"), {
    target: { value: "password" },
  });
  fireEvent.click(
    screen.getByRole("button", { name: "Restablecer contraseña" }),
  );
  expect(
    await screen.findByText("Contraseña demasiado común."),
  ).toBeInTheDocument();
  fireEvent.click(
    screen.getByRole("button", { name: "Restablecer contraseña" }),
  );
  expect(await screen.findByText(/enlace no es válido/)).toBeInTheDocument();
});

test("enlace sin parámetros no muestra formulario y ofrece solicitar otro", () => {
  window.history.replaceState(null, "", "/reset-password");
  show(<ResetPasswordPage />);
  expect(screen.getByRole("alert")).toHaveTextContent("enlace no es válido");
  expect(
    screen.getByRole("link", { name: "Solicitar otro enlace" }),
  ).toHaveAttribute("href", "/forgot-password");
  expect(api).not.toHaveBeenCalled();
});

test("solicitud con error de red muestra mensaje general", async () => {
  vi.mocked(api).mockRejectedValue(new Error("internal details"));
  show(<ForgotPasswordPage />);
  fireEvent.change(screen.getByLabelText("Correo electrónico"), {
    target: { value: "synthetic@example.test" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Enviar instrucciones" }));
  expect(await screen.findByRole("alert")).toHaveTextContent(
    "No fue posible procesar la solicitud",
  );
  expect(screen.queryByText("internal details")).not.toBeInTheDocument();
});
