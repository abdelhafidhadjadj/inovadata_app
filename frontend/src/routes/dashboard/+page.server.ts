import { redirect, fail } from '@sveltejs/kit';
import type { PageServerLoad, Actions } from './$types';
import { projects } from '$lib/server/projects';

export const load: PageServerLoad = async ({ locals }) => {
  if (!locals.user) {
    throw redirect(303, '/login');
  }

  try {
    const userProjects = await projects.getUserProjects(locals.user.id);

    return {
      projects: userProjects
    };
  } catch (error) {
    console.error('Load dashboard error:', error);
    return {
      projects: []
    };
  }
};

export const actions: Actions = {
  createProject: async ({ request, locals }) => {
    if (!locals.user) {
      return fail(401, { error: 'Unauthorized' });
    }

    const formData = await request.formData();
    const name = formData.get('name')?.toString();
    const description = formData.get('description')?.toString();
    const isPublic = formData.get('is_public') === 'true';

    if (!name) {
      return fail(400, { error: 'Project name is required' });
    }

    if (name.length < 3) {
      return fail(400, { error: 'Project name must be at least 3 characters' });
    }

    try {
      const project = await projects.create(
        name,
        locals.user.id,
        description,
        isPublic
      );

      return { success: true, project };
    } catch (error) {
      console.error('Create project error:', error);
      return fail(500, { error: 'Failed to create project' });
    }
  }
};