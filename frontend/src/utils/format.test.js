import { describe, it, expect } from 'vitest';
import { formatINR } from './format';

describe('formatINR', () => {
  it('formats amounts in Indian numbering format', () => {
    const formatted = formatINR(150000).replace(/\u00a0/g, ' '); // normalize non-breaking spaces
    expect(formatted).toContain('1,50,000');
  });

  it('handles zero and null values gracefully', () => {
    expect(formatINR(0)).toContain('0');
    expect(formatINR(null)).toBe('₹0');
  });
});
