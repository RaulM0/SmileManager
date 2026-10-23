import { rmSync } from 'node:fs'
import { resolve } from 'node:path'

export default function globalTeardown() {
  const root = resolve(import.meta.dirname, '../..')
  rmSync(resolve(root, '.e2e.sqlite3'), { force: true })
  rmSync(resolve(root, '.e2e-media'), { recursive: true, force: true })
}
