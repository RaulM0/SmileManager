import { renderWithToast as render } from "../../test/renderWithToast";
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from 'react-router-dom';
import { afterEach, expect, test, vi } from 'vitest';
import { api } from '../../api/client';
import { BackofficeAppointments, BackofficePatients } from './BackofficeClinical';

vi.mock('../../api/client', () => ({ api: vi.fn() }));
afterEach(() => { cleanup(); vi.resetAllMocks(); });
function show(element: React.ReactNode, route = '/backoffice/patients') {
  return render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><MemoryRouter initialEntries={[route]}>{element}</MemoryRouter></QueryClientProvider>);
}

test('pacientes se filtran por médico y búsqueda en el servidor', async () => {
  vi.mocked(api).mockResolvedValue({ count: 1, next: null, previous: null, results: [{ id: 4, nombre: 'Sintético', appat: 'Prueba', apmat: '', medico: 'doctor', estatus: 'A' }] });
  show(<BackofficePatients />, '/backoffice/patients?doctor=8');
  expect(await screen.findByText(/Sintético Prueba/)).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText('Buscar pacientes'), { target: { value: 'Prueba' } });
  fireEvent.click(screen.getByRole('button', { name: 'Buscar' }));
  await waitFor(() => expect(api).toHaveBeenCalledWith(expect.stringContaining('doctor=8&search=Prueba')));
});

test('citas muestra estado vacío y filtro de estado', async () => {
  vi.mocked(api).mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  show(<BackofficeAppointments />);
  expect(await screen.findByText('No hay citas con este filtro.')).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText('Estado'), { target: { value: 'P' } });
  await waitFor(() => expect(api).toHaveBeenCalledWith(expect.stringContaining('state=P')));
});
