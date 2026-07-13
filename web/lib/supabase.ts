import { createClient } from '@supabase/supabase-js';

// Client Supabase (lecture publique via anon key). Côté serveur (Server Components).
export function supabase() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !key) return null; // app affiche un état "non configuré" plutôt que planter
  return createClient(url, key, { auth: { persistSession: false } });
}
