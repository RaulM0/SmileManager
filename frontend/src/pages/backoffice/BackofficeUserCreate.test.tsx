import { renderWithToast as render } from "../../test/renderWithToast";
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, expect, test, vi } from 'vitest';
import { api } from '../../api/client';
import { BackofficeUserCreate } from './BackofficeUserCreate';

vi.mock('../../api/client', () => ({ api: vi.fn(), ApiError: class extends Error {} }));
vi.mock('../../components/ConfirmDialog', () => ({ ConfirmDialog: ({ onConfirm }: { onConfirm: () => void }) => <div role="dialog"><button onClick={onConfirm}>Confirmar creación</button></div> }));
afterEach(() => { cleanup(); vi.resetAllMocks(); });

test('crear usuario requiere confirmación antes de enviar', async () => {
  vi.mocked(api).mockResolvedValue({ id: 7 });
  render(<QueryClientProvider client={new QueryClient()}><MemoryRouter initialEntries={['/backoffice/users/new']}><Routes><Route path="/backoffice/users/new" element={<BackofficeUserCreate />} /><Route path="/backoffice/users/:id" element={<p>Usuario creado</p>} /></Routes></MemoryRouter></QueryClientProvider>);
  fireEvent.change(screen.getByLabelText('Usuario'), { target: { value: 'doctor' } });
  fireEvent.change(screen.getByLabelText('Correo electrónico'), { target: { value: 'doctor@example.test' } });
  fireEvent.change(screen.getByLabelText('Contraseña inicial'), { target: { value: 'synthetic passphrase 123!' } });
  fireEvent.click(screen.getByRole('button', { name: 'Crear usuario' }));
  expect(api).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'Confirmar creación' }));
  await waitFor(() => expect(api).toHaveBeenCalledTimes(1));
  expect(await screen.findByText('Usuario creado')).toBeInTheDocument();
});
