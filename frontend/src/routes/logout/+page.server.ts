import { redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { auth } from '$lib/server/auth';

export const load: PageServerLoad = async ({ locals, cookies }) => {
  if (locals.sessionId) {
    await auth.deleteSession(locals.sessionId);
  }
  
  cookies.delete('session_id', { path: '/' });
  
  throw redirect(303, '/login');
};