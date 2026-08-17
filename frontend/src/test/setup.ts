import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'
import '@testing-library/jest-dom/vitest'

// `globals: true` isn't set in vitest.config.ts (tests import describe/it/
// expect/vi explicitly), so @testing-library/react's automatic afterEach
// cleanup doesn't register itself. Do it here instead.
afterEach(() => {
  cleanup()
})
