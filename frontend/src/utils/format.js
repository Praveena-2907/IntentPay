/**
 * Format an integer rupee amount into Indian locale string: e.g. 150000 -> "₹1,50,000"
 * @param {number|string} amount
 * @returns {string}
 */
export function formatINR(amount) {
  if (amount === null || amount === undefined || isNaN(Number(amount))) {
    return '₹0';
  }
  const num = Math.round(Number(amount));
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(num);
}

/**
 * Format a timestamp into a clean machine-readable string
 * @param {string|Date} dateStr
 * @returns {string}
 */
export function formatTimestamp(dateStr) {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;
  return d.toISOString().replace('T', ' ').substring(0, 19);
}

export const formatRupees = formatINR;
export const formatDateTime = formatTimestamp;
