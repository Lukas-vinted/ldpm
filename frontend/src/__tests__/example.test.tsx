/**
 * Example test to verify vitest setup is working correctly.
 */
import { describe, it, expect } from 'vitest'

describe('Example Tests', () => {
  it('should perform simple arithmetic', () => {
    const result = 1 + 1
    expect(result).toBe(2)
  })

  it('should handle string operations', () => {
    const greeting = 'Hello'
    const name = 'LDPM'
    const message = `${greeting} ${name}`
    expect(message).toBe('Hello LDPM')
  })

  it('should work with arrays', () => {
    const items = ['test', 'vitest', 'setup']
    expect(items).toHaveLength(3)
    expect(items[0]).toBe('test')
  })
})
