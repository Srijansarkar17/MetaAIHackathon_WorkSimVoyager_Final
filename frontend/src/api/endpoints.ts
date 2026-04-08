export const BACKEND_URL = import.meta.env.VITE_BACKEND_URL ?? 'https://aditya9981-meta-hackthon-worksim-voyager.hf.space'

export const API_PATHS = {
  reset: '/reset',
  step: '/step',
  state: '/state',
  schema: '/schema',
  health: '/health',
} as const
