/** Format a number as USD, e.g. formatUSD(2500) -> "$2,500" */
export function formatUSD(value) {
  if (value == null) return '—'
  return `$${Number(value).toLocaleString('en-US')}`
}

/** Format a USD salary range, falling back to "Thỏa thuận" when negotiable */
export function formatSalaryRange(min, max, raw) {
  if (raw === 'Thỏa thuận') return 'Thỏa thuận'
  if (min && max) return `${formatUSD(min)} – ${formatUSD(max)}`
  if (max) return `Up to ${formatUSD(max)}`
  if (min) return `From ${formatUSD(min)}`
  return 'Thỏa thuận'
}

/** Simple Vietnamese-locale date formatter, e.g. "18 thg 6, 2026" */
export function formatDateVN(date) {
  return new Date(date).toLocaleDateString('vi-VN', {
    day: 'numeric', month: 'short', year: 'numeric',
  })
}

/** Truncate long text with an ellipsis */
export function truncate(text, max = 120) {
  if (!text || text.length <= max) return text
  return `${text.slice(0, max).trimEnd()}…`
}
