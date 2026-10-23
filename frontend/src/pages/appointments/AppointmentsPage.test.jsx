import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, test, vi } from 'vitest'
import { AppointmentCalendar } from './AppointmentsPage'

describe('AppointmentCalendar', () => {
  test('muestra las citas y permite navegar entre meses', () => {
    vi.setSystemTime(new Date(2026, 9, 23, 12))
    render(<MemoryRouter><AppointmentCalendar appointments={[{ id: 7, fecha: '2026-10-24', hora: '10:00:00', estatus: 'P', paciente: { full_name: 'ANA LOPEZ' } }]} /></MemoryRouter>)
    expect(screen.getByRole('heading', { name: /octubre de 2026/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /10:00 ANA LOPEZ/ })).toHaveAttribute('href', '/appointments/7')
    fireEvent.click(screen.getByRole('button', { name: 'Mes siguiente' }))
    expect(screen.getByRole('heading', { name: /noviembre de 2026/i })).toBeInTheDocument()
    vi.useRealTimers()
  })
})
