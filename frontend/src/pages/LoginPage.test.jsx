import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { expect, test, vi } from 'vitest'
import LoginPage from './LoginPage'

vi.mock('../context/AuthContext', () => ({ useAuth: () => ({ user:null, loading:false, login:vi.fn() }) }))

test('conserva los campos y acciones del login legacy', () => {
  render(<MemoryRouter><LoginPage /></MemoryRouter>)
  expect(screen.getByLabelText('Usuario')).toBeRequired()
  expect(screen.getByLabelText('Contraseña')).toBeRequired()
  expect(screen.getByRole('button', {name:/iniciar sesión/i})).toBeInTheDocument()
  expect(screen.getByText(/análisis con inteligencia artificial/i)).toBeInTheDocument()
})
