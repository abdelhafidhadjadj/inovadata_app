import { redirect, type Handle } from '@sveltejs/kit';
import { auth } from '$lib/server/auth';

export const handle: Handle = async ({ event, resolve }) => {
  // Get session from cookie
  const sessionId = event.cookies.get('session');

  if (sessionId) {
    try {
      // Validate session and get user
      const user = await auth.validateSession(sessionId);
      if (user) {
        event.locals.user = user;
      } else {
        // Invalid session, delete cookie
        event.cookies.delete('session', { path: '/' });
      }
    } catch (error) {
      console.error('Session validation error:', error);
      event.cookies.delete('session', { path: '/' });
    }
  }

  // Protected routes
  const protectedRoutes = ['/dashboard', '/projects', '/datasets', '/models'];
  const isProtectedRoute = protectedRoutes.some(route => 
    event.url.pathname.startsWith(route)
  );

  // Redirect to login if accessing protected route without authentication
  if (isProtectedRoute && !event.locals.user) {
    throw redirect(303, '/login');
  }

  // Redirect to dashboard if accessing login/register while authenticated
  if ((event.url.pathname === '/login' || event.url.pathname === '/register') && event.locals.user) {
    throw redirect(303, '/dashboard');
  }

  const response = await resolve(event);
  return response;
};