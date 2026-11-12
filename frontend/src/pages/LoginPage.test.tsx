import { render, screen, fireEvent, waitFor, cleanup } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { api } from "../api/client";
import LoginPage from "./LoginPage";
import { ToastProvider } from "../context/ToastContext";

const { login, completeLogin } = vi.hoisted(() => ({ login: vi.fn(), completeLogin: vi.fn() }));
vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({ user: null, loading: false, login, completeLogin }),
}));
vi.mock("../api/client", () => ({ api: vi.fn(), getErrorMessage: (error: Error) => error.message }));
beforeEach(() => { vi.resetAllMocks(); });
afterEach(cleanup);

test("conserva los campos y acciones del login legacy", () => {
  render(
    <ToastProvider><MemoryRouter>
      <LoginPage />
    </MemoryRouter></ToastProvider>,
  );
  expect(screen.getByLabelText("Usuario")).toBeRequired();
  expect(screen.getByLabelText("Contraseña")).toBeRequired();
  expect(
    screen.getByRole("button", { name: /iniciar sesión/i }),
  ).toBeInTheDocument();
  expect(
    screen.getByText(/análisis con inteligencia artificial/i),
  ).toBeInTheDocument();
});


test("configura MFA mediante QR y envía el código antes de mostrar la recuperación", async () => {
  const uri = 'otpauth://totp/SmileManager:demo?secret=JBSWY3DPEHPK3PXP&issuer=SmileManager';
  login.mockResolvedValue({ mfa_required: true, enrollment_required: true, challenge: 'challenge-demo' });
  vi.mocked(api).mockResolvedValueOnce({ otpauth_uri: uri }).mockResolvedValueOnce({ recovery_codes: ['recovery-demo'] });
  render(<ToastProvider><MemoryRouter><LoginPage /></MemoryRouter></ToastProvider>);
  fireEvent.change(screen.getByLabelText("Usuario"), { target: { value: "demo" } });
  fireEvent.change(screen.getByLabelText("Contraseña"), { target: { value: "password" } });
  fireEvent.click(screen.getByRole("button", { name: "Iniciar sesión" }));
  const qr = await screen.findByRole("img", { name: "Código QR para configurar tu autenticador" });
  expect(qr.tagName.toLowerCase()).toBe("svg");
  expect(qr.querySelector("path")).not.toBeNull();
  expect(screen.queryByText("JBSWY3DPEHPK3PXP")).not.toBeInTheDocument();
  fireEvent.change(screen.getByLabelText("Código del autenticador"), { target: { value: "123456" } });
  fireEvent.click(screen.getByRole("button", { name: "Verificar" }));
  await screen.findByRole("region", { name: "Códigos de recuperación" });
  expect(api).toHaveBeenLastCalledWith('auth/mfa/verify/', { method: 'POST', body: JSON.stringify({ challenge: 'challenge-demo', code: '123456' }) });
  expect(completeLogin).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "He guardado los códigos" }));
  await waitFor(() => expect(completeLogin).toHaveBeenCalledWith({ recovery_codes: ['recovery-demo'] }));
});

test("volver al login retira el QR y el campo del segundo factor", async () => {
  login.mockResolvedValue({ mfa_required: true, enrollment_required: true, challenge: 'challenge-demo' });
  vi.mocked(api).mockResolvedValueOnce({ otpauth_uri: 'otpauth://totp/demo?secret=JBSWY3DPEHPK3PXP' });
  render(<ToastProvider><MemoryRouter><LoginPage /></MemoryRouter></ToastProvider>);
  fireEvent.submit(screen.getByRole("button", { name: "Iniciar sesión" }).closest("form")!);
  await screen.findByRole("img", { name: "Código QR para configurar tu autenticador" });
  fireEvent.click(screen.getByRole("button", { name: "Volver al inicio de sesión" }));
  expect(screen.queryByRole("img")).not.toBeInTheDocument();
  expect(screen.getByLabelText("Contraseña")).toHaveValue("");
});
