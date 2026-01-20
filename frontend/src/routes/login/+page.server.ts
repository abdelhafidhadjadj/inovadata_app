import { fail, redirect } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';
import { auth } from '$lib/server/auth';
import { db } from '$lib/server/db';

export const load: PageServerLoad = async ({ locals }) => {
  // Redirect if already logged in
  if (locals.user) {
    throw redirect(303, '/dashboard');
  }
  return {};
};

export const actions: Actions = {
  default: async ({ request, cookies }) => {
    const formData = await request.formData();
    const usernameOrEmail = formData.get('username')?.toString();
    const password = formData.get('password')?.toString();

    // Validation
    if (!usernameOrEmail || !password) {
      return fail(400, {
        error: 'Username/email and password are required',
        username: usernameOrEmail
      });
    }

    try {
      // Find user
      const user = await auth.findUser(usernameOrEmail);
      
      if (!user) {
        return fail(401, {
          error: 'Invalid username/email or password',
          username: usernameOrEmail
        });
      }

      // Get password hash
      const result = await db.query(
        'SELECT password_hash FROM users WHERE id = $1',
        [user.id]
      );

      if (result.rows.length === 0) {
        return fail(401, {
          error: 'Invalid username/email or password',
          username: usernameOrEmail
        });
      }

      // Verify password
      const isValid = await auth.verifyPassword(password, result.rows[0].password_hash);

      if (!isValid) {
        return fail(401, {
          error: 'Invalid username/email or password',
          username: usernameOrEmail
        });
      }

      // Check if user is active
      if (!user.is_active) {
        return fail(403, {
          error: 'Your account has been deactivated',
          username: usernameOrEmail
        });
      }

      // Create session
      const sessionId = await auth.createSession(user.id);

      // Set session cookie
      cookies.set('session', sessionId, {
        path: '/',
        httpOnly: true,
        sameSite: 'lax',
        secure: false, // Development only
        maxAge: 60 * 60 * 24 * 7 // 7 days
      });

      // Redirect to dashboard
      throw redirect(303, '/dashboard');
      
    } catch (error: any) {
      // IMPORTANT: Re-throw redirects immediately, don't log them
      if (error?.status === 303 || error?.status === 302 || error?.status === 301) {
        throw error;
      }

      // Only log actual errors
      console.error('Login error:', error);
      
      return fail(500, {
        error: 'An error occurred during login',
        username: usernameOrEmail
      });
    }
  }
};