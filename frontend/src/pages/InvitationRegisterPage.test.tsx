import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { expect, test, vi } from "vitest";
import { api } from "../api/client";
import InvitationRegisterPage from "./InvitationRegisterPage";

vi.mock("../api/client", () => ({ api: vi.fn(), getErrorMessage: (error: Error) => error.message }));

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
