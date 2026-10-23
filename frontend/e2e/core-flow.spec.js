import { expect, test } from '@playwright/test'
import { Buffer } from 'node:buffer'

const tinyImage = {
  name: 'clinical.png',
  mimeType: 'image/png',
  buffer: Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=', 'base64'),
}

test('flujo clínico completo de React contra la API', async ({ page }) => {
  test.setTimeout(90_000)
  const unique = String(Date.now()).slice(-9)
  const phone = `9${unique}`
  const name = `E2E${unique}`

  await page.goto('login')
  await page.getByLabel('Usuario').fill('e2e_doctor')
  await page.getByLabel('Contraseña').fill('e2e_password_123')
  await page.getByRole('button', { name: 'Iniciar sesión' }).click()
  await expect(page.getByText(/Bienvenido, Dr. E2E_DOCTOR/)).toBeVisible()
  await page.getByRole('link', { name: 'Aviso de Privacidad' }).click()
  await expect(page.getByRole('heading', { name: /Aviso de Privacidad/ })).toBeVisible()

  await page.getByRole('link', { name: /Pacientes/ }).first().click()
  await expect(page.getByRole('heading', { name: 'Gestión de pacientes' })).toBeVisible()
  await page.getByRole('link', { name: 'Acceder' }).nth(1).click()
  await page.getByLabel('Nombre').fill(name)
  await page.getByLabel('Apellido paterno').fill('PRUEBA')
  await page.getByLabel('Apellido materno').fill('REACT')
  await page.getByLabel('Fecha de nacimiento').fill('1990-01-01')
  await page.getByLabel('Género').selectOption('F')
  await page.getByLabel('Teléfono').fill(phone)
  await page.getByLabel('Correo electrónico').fill(`${name.toLowerCase()}@example.com`)
  await page.getByRole('button', { name: 'Registrar paciente' }).click()
  await expect(page.getByRole('heading', { name: new RegExp(name) })).toBeVisible()
  const patientId = page.url().match(/patients\/(\d+)/)?.[1]
  expect(patientId).toBeTruthy()

  await page.goto(`/app/patients/${patientId}/edit`)
  await page.getByLabel('Apellido materno').fill('MIGRADO')
  await page.getByRole('button', { name: 'Guardar cambios' }).click()
  await expect(page.getByRole('heading', { name: /MIGRADO/ })).toBeVisible()

  await page.goto(`/app/patients/search?q=${name}`)
  await expect(page.getByRole('cell', { name: `${name} PRUEBA MIGRADO`, exact: true })).toBeVisible()

  await page.goto(`/app/patients/${patientId}/medical-history`)
  await page.locator('#tratamiento_medico-yes').check({ force: true })
  await page.getByLabel('Alergias').fill('NINGUNA')
  await page.getByRole('button', { name: 'Guardar antecedentes' }).click()
  await expect(page.getByText('Antecedentes actualizados')).toBeVisible()

  await page.goto(`/app/patients/${patientId}/consultations/new`)
  await page.getByLabel('Motivo de consulta').fill('CONTROL E2E')
  await page.getByLabel('Diagnóstico').fill('DIAGNOSTICO E2E')
  await page.getByLabel('Tratamiento').fill('TRATAMIENTO E2E')
  await page.getByRole('button', { name: 'Registrar consulta' }).click()
  await expect(page.getByRole('heading', { name: 'Receta médica' })).toBeVisible()
  await expect(page.getByText('DIAGNOSTICO E2E')).toBeVisible()

  await page.goto(`/app/patients/${patientId}/consultations`)
  await expect(page.getByRole('cell', { name: 'CONTROL E2E' })).toBeVisible()

  await page.goto(`/app/patients/${patientId}/images/upload`)
  await page.getByLabel('Consulta').selectOption({ index: 1 })
  await page.getByLabel('Tipo de imagen').fill('RADIOGRAFIA')
  await page.getByLabel('Descripción').fill('IMAGEN E2E')
  await page.getByLabel('Archivo').setInputFiles(tinyImage)
  await page.getByRole('button', { name: 'Cargar imagen' }).click()
  await expect(page.getByText('IMAGEN E2E')).toBeVisible()
  await page.goto(`/app/patients/${patientId}/images`)
  await expect(page.getByRole('heading', { name: 'Imágenes clínicas' })).toBeVisible()
  await page.getByRole('heading', { name: 'Buscar imágenes' }).click()
  await page.getByLabel('Consulta').selectOption({ index: 1 })
  await expect(page.getByText('IMAGEN E2E')).toBeVisible()

  await page.goto(`/app/patients/${patientId}/odontogram`)
  await page.getByRole('button', { name: 'Caries', exact: true }).click()
  await page.getByRole('button', { name: '18 oclusal sano' }).click()
  await page.getByRole('button', { name: 'Guardar odontograma' }).click()
  await expect(page.getByText('Odontograma guardado correctamente.')).toBeVisible()
  await expect(page.getByText('Caries: 1')).toBeVisible()

  await page.goto(`/app/patients/${patientId}/comparative-study`)
  await page.getByLabel('Fecha de inicio').fill('2026-01-01')
  await page.getByLabel('Diagnóstico').fill('ESTUDIO E2E')
  for (const label of ['Oclusal superior', 'Lateral izquierda', 'Frontal', 'Lateral derecha', 'Oclusal inferior']) {
    await page.getByLabel(label, { exact: true }).setInputFiles(tinyImage)
  }
  await page.getByRole('button', { name: 'Guardar estudio' }).click()
  await expect(page.getByText('Estudio guardado correctamente.')).toBeVisible()
  const pdfPromise = page.waitForEvent('download')
  await page.getByRole('link', { name: /Descargar PDF/ }).click()
  expect((await pdfPromise).suggestedFilename()).toMatch(/^Estudio_.*\.pdf$/)

  await page.goto(`/app/patients/${patientId}/consent`)
  await page.getByLabel('He leído y acepto los términos.').check()
  await page.getByLabel('Identificación oficial').setInputFiles(tinyImage)
  await page.getByRole('button', { name: 'Aceptar y guardar' }).click()
  await expect(page.getByRole('heading', { name: 'Consentimiento aceptado' })).toBeVisible()

  await page.goto('/app/diagnostics')
  await page.getByLabel('Paciente').fill(name)
  await page.getByRole('button', { name: 'Filtrar' }).click()
  await expect(page.getByRole('heading', { name: `${name} PRUEBA`, exact: true })).toBeVisible()
  await page.getByRole('link', { name: 'Analizar' }).click()
  await expect(page.getByRole('heading', { name: /Resultados de análisis/ })).toBeVisible()
  await expect(page.getByText('Procesando imagen con YOLO…')).toBeHidden({ timeout: 30_000 })
  await expect(page.getByText('Imagen analizada')).toBeVisible()
  await expect(page.locator('.alert-danger')).toHaveCount(0)
  await expect(page.locator('.image-viewer')).toHaveCount(2)

  await page.goto(`/app/patients/${patientId}/images/history`)
  page.once('dialog', dialog => dialog.accept())
  await page.getByRole('button', { name: 'Eliminar' }).click()
  await expect(page.getByText('No hay imágenes clínicas.')).toBeVisible()

  await page.goto('/app/exports')
  const exportNames = ['Pacientes.xlsx', 'Consultas.xlsx', 'ImagenesClinicas.xlsx']
  for (const filename of exportNames) {
    const downloadPromise = page.waitForEvent('download')
    await page.getByRole('link', { name: 'Descargar Excel' }).nth(exportNames.indexOf(filename)).click()
    expect((await downloadPromise).suggestedFilename()).toBe(filename)
  }

  await page.goto('/app/patients/contact')
  await page.getByLabel('Buscar paciente por nombre').fill(name)
  await page.getByRole('button', { name: new RegExp(name) }).click()
  await page.getByLabel('Asunto').fill('MENSAJE E2E')
  await page.getByLabel('Mensaje').fill('VALIDACION DE CORREO')
  await page.getByRole('button', { name: 'Enviar correo' }).click()
  await expect(page.getByText(/Correo enviado exitosamente/)).toBeVisible()

  await page.getByRole('link', { name: /Citas/ }).click()
  await page.getByRole('link', { name: /Nueva cita/ }).click()
  await page.getByLabel('Buscar paciente por nombre').fill(name)
  await page.getByRole('button', { name: new RegExp(name) }).click()
  const tomorrow = new Date()
  tomorrow.setDate(tomorrow.getDate() + 1)
  await page.getByLabel('Fecha').fill(tomorrow.toISOString().slice(0, 10))
  await page.getByLabel('Hora').fill('10:00')
  await page.getByLabel('Motivo').fill('Control E2E')
  await page.getByRole('button', { name: 'Registrar cita' }).click()
  await expect(page.getByRole('heading', { name: /Detalle de cita/ })).toBeVisible()
  await expect(page.getByText('Control E2E')).toBeVisible()
  const appointmentId = page.url().match(/appointments\/(\d+)/)?.[1]

  await page.goto(`/app/appointments/${appointmentId}/edit`)
  await page.getByLabel('Motivo').fill('Control E2E editado')
  await page.getByRole('button', { name: 'Guardar cambios' }).click()
  await expect(page.getByText('Control E2E editado')).toBeVisible()

  await page.goto('/app/appointments')
  await expect(page.getByRole('region', { name: 'Calendario de citas' })).toBeVisible()
  await page.getByRole('button', { name: 'Completar' }).last().click()
  await expect(page.getByText('Completada').last()).toBeVisible()

  await page.goto(`/app/patients/${patientId}`)
  page.once('dialog', dialog => dialog.accept())
  await page.getByRole('button', { name: 'Desactivar' }).click()
  await expect(page).toHaveURL(/patients\/search/)

  await page.getByRole('button', { name: /Salir/ }).click()
  await expect(page).toHaveURL(/\/app\/login$/)
})

test('navegación móvil conserva el menú legacy', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('login')
  await page.getByLabel('Usuario').fill('e2e_doctor')
  await page.getByLabel('Contraseña').fill('e2e_password_123')
  await page.getByRole('button', { name: 'Iniciar sesión' }).click()
  await page.getByRole('button', { name: 'Abrir navegación' }).click()
  await expect(page.getByRole('link', { name: /Pacientes/ })).toBeVisible()
  await expect(page.getByRole('link', { name: /Diagnósticos/ })).toBeVisible()
})
