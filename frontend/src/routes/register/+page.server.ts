import { fail, redirect } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types';
import { auth } from '$lib/server/auth';

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
    const fullName = formData.get('full_name')?.toString() || undefined;
    const username = formData.get('username')?.toString();
    const email = formData.get('email')?.toString();
    const password = formData.get('password')?.toString();
    const confirmPassword = formData.get('confirm_password')?.toString();

    // Validation
    if (!username || !email || !password || !confirmPassword) {
      return fail(400, {
        error: 'Username, email, and password are required',
        username,
        email,
        fullName
      });
    }

    // Check password match
    if (password !== confirmPassword) {
      return fail(400, {
        error: 'Passwords do not match',
        username,
        email,
        fullName
      });
    }

    // Validate username format
    if (!/^[a-zA-Z0-9_]+$/.test(username)) {
      return fail(400, {
        error: 'Username can only contain letters, numbers, and underscores',
        username,
        email,
        fullName
      });
    }

    // Validate username length
    if (username.length < 3) {
      return fail(400, {
        error: 'Username must be at least 3 characters long',
        username,
        email,
        fullName
      });
    }

    // Validate password length
    if (password.length < 8) {
      return fail(400, {
        error: 'Password must be at least 8 characters long',
        username,
        email,
        fullName
      });
    }

    try {
      // Check if username exists
      const existingUser = await auth.findUser(username);
      if (existingUser) {
        return fail(400, {
          error: 'Username already taken',
          email,
          fullName
        });
      }

      // Check if email exists
      const existingEmail = await auth.findUser(email);
      if (existingEmail) {
        return fail(400, {
          error: 'Email already registered',
          username,
          fullName
        });
      }

      // Create user (this handles password hashing internally)
      const user = await auth.createUser(username, email, password, fullName);

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
      // Re-throw redirects
      if (error?.status === 303 || error?.status === 302 || error?.status === 301) {
        throw error;
      }

      // Log actual errors
      console.error('Registration error:', error);
      
      return fail(500, {
        error: 'An error occurred during registration. Please try again.',
        username,
        email,
        fullName
      });
    }
  }
};