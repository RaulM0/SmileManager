import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { afterEach, expect, test, vi } from 'vitest';
import { api } from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import { BackofficeAudit, BackofficeDashboard, BackofficeLayout, BackofficeRuns, BackofficeSystem, BackofficeUsers } from './Backoffice';

vi.mock('../../api/client', () => ({ api: vi.fn(), getErrorMessage: () => 'Error' }));
vi.mock('../../context/AuthContext', () => ({ useAuth: vi.fn() }));
afterEach(() => { cleanup(); vi.resetAllMocks(); });

function show() {
  return render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><MemoryRouter initialEntries={['/backoffice']}><Routes><Route path="/backoffice" element={<BackofficeLayout />}><Route index element={<BackofficeDashboard />} /></Route></Routes></MemoryRouter></QueryClientProvider>);
}

test('usuario normal no ve datos administrativos', () => {
  vi.mocked(useAuth).mockReturnValue({ user: { id: 1, username: 'normal', can_access_backoffice: false } } as ReturnType<typeof useAuth>);
  show();
  expect(screen.getByRole('heading', { name: 'Acceso no autorizado' })).toBeInTheDocument();
  expect(api).not.toHaveBeenCalled();
});

test('administrador ve el resumen operativo', async () => {
  vi.mocked(useAuth).mockReturnValue({ user: { id: 1, username: 'admin', can_access_backoffice: true } } as ReturnType<typeof useAuth>);
  vi.mocked(api).mockResolvedValue({ users: { active: 3, inactive: 1 }, ai: { running: 0, failed: 2, stale: 0 }, recent_admin_events: [] });
  show();
  expect(screen.getByRole('status')).toHaveTextContent('Cargando');
  expect(await screen.findByText('Usuarios activos')).toBeInTheDocument();
  expect(screen.getByText('Aún no hay acciones administrativas.')).toBeInTheDocument();
});

test('error del resumen se presenta sin detalles internos', async () => {
  vi.mocked(useAuth).mockReturnValue({ user: { id: 1, username: 'admin', can_access_backoffice: true } } as ReturnType<typeof useAuth>);
  vi.mocked(api).mockRejectedValue(new Error('internal path'));
  show();
  expect(await screen.findByRole('alert')).toHaveTextContent('No fue posible cargar la información');
  expect(screen.queryByText('internal path')).not.toBeInTheDocument();
});

function showPage(element: React.ReactNode) {
  vi.mocked(useAuth).mockReturnValue({ user: { id: 1, username: 'admin', can_access_backoffice: true } } as ReturnType<typeof useAuth>);
  return render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}><MemoryRouter>{element}</MemoryRouter></QueryClientProvider>);
}

test('usuarios busca, filtra y solicita la siguiente página al servidor', async () => {
  vi.mocked(api).mockResolvedValue({ count: 30, next: 'next', previous: null, results: [{ id: 2, username: 'doctor', email: '', is_active: true }] });
  showPage(<BackofficeUsers />);
  await screen.findByText('doctor');
  fireEvent.change(screen.getByLabelText('Buscar usuario'), { target: { value: 'doc' } });
  fireEvent.click(screen.getByRole('button', { name: 'Buscar' }));
  await waitFor(() => expect(api).toHaveBeenCalledWith(expect.stringContaining('search=doc')));
  fireEvent.change(screen.getByLabelText('Estado'), { target: { value: 'active' } });
  await waitFor(() => expect(api).toHaveBeenCalledWith(expect.stringContaining('state=active')));
  fireEvent.click(screen.getByRole('button', { name: 'Siguiente' }));
  await waitFor(() => expect(api).toHaveBeenCalledWith(expect.stringContaining('page=2')));
});

test('auditoría aplica filtros al servidor', async () => {
  vi.mocked(api).mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  showPage(<BackofficeAudit />);
  await screen.findByText('No hay eventos con este filtro.');
  fireEvent.change(screen.getByLabelText('Acción'), { target: { value: 'USER_ACTIVATED' } });
  fireEvent.click(screen.getByRole('button', { name: 'Aplicar filtros' }));
  await waitFor(() => expect(api).toHaveBeenCalledWith(expect.stringContaining('action=USER_ACTIVATED')));
});

test('IA filtra y sistema muestra disponibilidad', async () => {
  vi.mocked(api).mockResolvedValue({ count: 0, next: null, previous: null, results: [] });
  const view = showPage(<BackofficeRuns />);
  await screen.findByText('No hay ejecuciones de IA con este filtro.');
  fireEvent.change(screen.getByLabelText('Estado'), { target: { value: 'FAILED' } });
  await waitFor(() => expect(api).toHaveBeenCalledWith(expect.stringContaining('status=FAILED')));
  view.unmount();
  vi.mocked(api).mockResolvedValue({ application: 'ok', database: 'ok', ai: 'not_checked' });
  showPage(<BackofficeSystem />);
  expect(await screen.findByText('Base de datos')).toBeInTheDocument();
  expect(screen.getAllByText('Disponible')).toHaveLength(2);
});
