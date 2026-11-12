import { renderWithToast as render } from "../test/renderWithToast";
import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { api, ApiError } from "../api/client";
import InvitationRegisterPage from "./InvitationRegisterPage";

vi.mock("../api/client", async (importOriginal) => ({ ...await importOriginal<typeof import('../api/client')>(), api: vi.fn() }));
beforeEach(() => vi.resetAllMocks());
afterEach(cleanup);

test("crea la cuenta únicamente al enviar el formulario", async () => {
  vi.mocked(api).mockResolvedValueOnce({ clinic: "Clínica A", role: "DOCTOR" }).mockResolvedValueOnce(undefined);
  render(<MemoryRouter initialEntries={["/invitations/register#token"]}><Routes><Route path="/invitations/register" element={<InvitationRegisterPage />} /></Routes></MemoryRouter>);
  fireEvent.change(screen.getByLabelText("Usuario"), { target: { value: "doctor" } });
  fireEvent.change(screen.getByLabelText("Contraseña"), { target: { value: "contraseña-segura" } });
  expect(await screen.findByText("Clínica A")).toBeInTheDocument();
  expect(api).toHaveBeenCalledTimes(1);
  fireEvent.click(screen.getByRole("button", { name: "Crear cuenta y aceptar invitación" }));
  await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Cuenta creada"));
  expect(api).toHaveBeenCalledTimes(2);
});


test("muestra el detalle de validación y permite corregirlo sin perder la invitación", async () => {
  vi.mocked(api).mockResolvedValueOnce({ clinic: "Clínica A", role: "CLINIC_ADMIN" })
    .mockRejectedValueOnce(new ApiError("No fue posible completar la operación.", 400, { detail: ["La contraseña es demasiado común."] }))
    .mockResolvedValueOnce(undefined);
  render(<MemoryRouter initialEntries={["/invitations/register#token"]}><InvitationRegisterPage /></MemoryRouter>);
  expect(await screen.findByText("Administrador de clínica")).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText("Usuario"), { target: { value: "clinica1" } });
  fireEvent.change(screen.getByLabelText("Contraseña"), { target: { value: "password" } });
  fireEvent.click(screen.getByRole("button", { name: "Crear cuenta y aceptar invitación" }));
  expect(await screen.findByRole("alert")).toHaveTextContent("La contraseña es demasiado común.");
  fireEvent.change(screen.getByLabelText("Contraseña"), { target: { value: "A stronger passphrase 492!" } });
  fireEvent.click(screen.getByRole("button", { name: "Crear cuenta y aceptar invitación" }));
  expect(await screen.findByRole("status")).toHaveTextContent("Cuenta creada");
});

test("muestra errores junto a los campos", async () => {
  vi.mocked(api).mockResolvedValueOnce({ clinic: "Clínica A", role: "DOCTOR" })
    .mockRejectedValueOnce(new ApiError("No fue posible completar la operación.", 400, { username: ["Ese usuario no está disponible."], password: ["Elige una contraseña más segura."] }));
  render(<MemoryRouter initialEntries={["/invitations/register#token"]}><InvitationRegisterPage /></MemoryRouter>);
  await screen.findByText("Clínica A");
  fireEvent.submit(screen.getByRole("button", { name: "Crear cuenta y aceptar invitación" }).closest('form')!);
  await screen.findByText("Ese usuario no está disponible.");
  expect(screen.getByLabelText('Usuario')).toHaveAttribute('aria-invalid', 'true');
  expect(screen.getByLabelText('Contraseña')).toHaveAttribute('aria-invalid', 'true');
});
