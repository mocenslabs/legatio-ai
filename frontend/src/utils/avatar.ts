/**
 * Deterministic fictional avatar (no upload required).
 * Uses DiceBear HTTP API — works offline-dev with network; fallback to initials SVG.
 */

const PALETTE = [
  '#0c8ce7',
  '#7c3aed',
  '#059669',
  '#d97706',
  '#db2777',
  '#4f46e5',
  '#0891b2',
  '#65a30d',
]

function hashString(input: string): number {
  let h = 0
  for (let i = 0; i < input.length; i++) {
    h = (h << 5) - h + input.charCodeAt(i)
    h |= 0
  }
  return Math.abs(h)
}

export function avatarColor(seed: string): string {
  return PALETTE[hashString(seed || 'user') % PALETTE.length]
}

export function initialsFromUser(opts: {
  first_name?: string
  last_name?: string
  email?: string
}): string {
  const first = (opts.first_name || '').trim()
  const last = (opts.last_name || '').trim()
  if (first || last) {
    return `${first.charAt(0)}${last.charAt(0)}`.toUpperCase() || first.slice(0, 2).toUpperCase()
  }
  const email = (opts.email || '?').trim()
  return email.slice(0, 2).toUpperCase()
}

export function displayNameFromUser(opts: {
  first_name?: string
  last_name?: string
  email?: string
}): string {
  const name = [opts.first_name, opts.last_name].filter(Boolean).join(' ').trim()
  return name || opts.email || 'User'
}

/** DiceBear “shapes” style — stable per seed (email or id). */
export function avatarUrl(seed: string, size = 64): string {
  const s = encodeURIComponent(seed || 'legatio')
  return `https://api.dicebear.com/9.x/shapes/svg?seed=${s}&size=${size}`
}
