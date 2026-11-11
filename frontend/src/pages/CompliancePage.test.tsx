import { act, cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { afterEach, expect, test, vi } from 'vitest';
import CompliancePage from './CompliancePage';
import { noticeFields } from '../types/compliance';

const request = vi.hoisted(() => vi.fn());
vi.mock('../api/client', () => ({ api: request, getClinicContext: () => 'clinic-a', getErrorMessage: (error: Error) => error.message }));
afterEach(() => { cleanup(); request.mockReset(); });

test('espera la configuración antes de editar y publica los cambios del usuario', async () => {
  let resolveNotice!: (value: unknown) => void;
  const pending = new Promise((resolve) => { resolveNotice = resolve; });
  const body = Object.fromEntries(noticeFields.map(([key]) => [key, key === 'privacy_email' ? 'privacy@example.test' : 'Texto sintético de prueba']));
  let notice = { id: 1, version: 1, published_at: '2026-01-01', body };
  let initial = true;
  request.mockImplementation((path: string, options?: RequestInit) => {
    if (options?.method === 'POST') { const payload = JSON.parse(String(options.body)); notice = { ...notice, version: 2, body: payload }; return Promise.resolve(notice); }
    if (path.includes('consent-templates')) return Promise.resolve([]);
    if (initial) { initial = false; return pending; }
    return Promise.resolve({ notice });
  });
  render(<MemoryRouter><CompliancePage /></MemoryRouter>);
  expect(screen.queryByLabelText('Nombre legal o razón social del responsable')).toBeNull();
  await act(async () => { resolveNotice({ notice }); });
  fireEvent.change(await screen.findByLabelText('Nombre legal o razón social del responsable'), { target: { value: 'Responsable revisado por el usuario' } });
  fireEvent.click(screen.getByLabelText('El responsable revisó estos datos y los procedimientos están disponibles para los titulares.'));
  fireEvent.submit(screen.getByRole('button', { name: 'Publicar nueva versión del aviso' }).closest('form')!);
  await waitFor(() => expect(request).toHaveBeenCalledWith('clinics/admin/privacy/', expect.objectContaining({ method: 'POST', body: expect.stringContaining('Responsable revisado por el usuario') })));
  expect(await screen.findByText('Aviso versión 2 publicado.')).toBeVisible();
});
