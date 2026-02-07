import { createClient } from '@supabase/supabase-js'

const url = import.meta.env.VITE_SUPABASE_URL || ''
const key = import.meta.env.VITE_SUPABASE_ANON_KEY || ''

const supabase = url && key && !url.includes('your_')
  ? createClient(url, key)
  : null

export default supabase
