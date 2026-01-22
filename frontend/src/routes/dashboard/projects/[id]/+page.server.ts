import { error, fail, redirect } from '@sveltejs/kit';
import type { PageServerLoad, Actions } from './$types';
import { projects } from '$lib/server/projects';
import { datasets } from '$lib/server/datasets';
import { experiments } from '$lib/server/experiments';

export const load: PageServerLoad = async ({ locals, params }) => {
  if (!locals.user) {
    throw redirect(303, '/login');
  }

  const projectId = parseInt(params.id);
  if (isNaN(projectId)) {
    throw error(400, 'Invalid project ID');
  }

  const project = await projects.getById(projectId, locals.user.id);
  if (!project) {
    throw error(404, 'Project not found');
  }

  const [projectDatasets, projectExperiments, members] = await Promise.all([
    datasets.getByProject(projectId, locals.user.id),
    experiments.getByProject(projectId, locals.user.id),
    projects.getMembers(projectId)
  ]);

  return {
    project,
    datasets: projectDatasets,
    experiments: projectExperiments,
    members
  };
};

export const actions: Actions = {
  updateProject: async ({ request, locals, params }) => {
    if (!locals.user) {
      return fail(401, { error: 'Unauthorized' });
    }

    const projectId = parseInt(params.id);
    const formData = await request.formData();
    const name = formData.get('name')?.toString();
    const description = formData.get('description')?.toString();
    const isPublic = formData.get('is_public') === 'true';

    if (!name) {
      return fail(400, { error: 'Project name is required' });
    }

    try {
      const updated = await projects.update(projectId, locals.user.id, {
        name,
        description,
        is_public: isPublic
      });

      if (!updated) {
        return fail(403, { error: 'Permission denied' });
      }

      return { success: true, message: 'Project updated successfully' };
    } catch (error) {
      console.error('Update project error:', error);
      return fail(500, { error: 'Failed to update project' });
    }
  },

  deleteProject: async ({ locals, params }) => {
  if (!locals.user) {
    return fail(401, { error: 'Unauthorized' });
  }

  const projectId = parseInt(params.id);

  try {
    const success = await projects.delete(projectId, locals.user.id);
    if (!success) {
      return fail(403, { error: 'Permission denied' });
    }
  } catch (err) {
    console.error('Delete project error:', err);
    return fail(500, { error: 'Failed to delete project' });
  }

  // Redirect happens outside try-catch (cleaner)
  throw redirect(303, '/dashboard');
},

  addMember: async ({ request, locals, params }) => {
    if (!locals.user) {
      return fail(401, { error: 'Unauthorized' });
    }

    const projectId = parseInt(params.id);
    const formData = await request.formData();
    const email = formData.get('email')?.toString();
    const role = formData.get('role')?.toString() as 'editor' | 'viewer';

    if (!email || !role) {
      return fail(400, { error: 'Email and role are required' });
    }

    if (!['editor', 'viewer'].includes(role)) {
      return fail(400, { error: 'Invalid role' });
    }

    try {
      const member = await projects.addMember(projectId, locals.user.id, email, role);
      if (!member) {
        return fail(404, { error: 'User not found or already a member' });
      }

      return { success: true, message: 'Member added successfully' };
    } catch (error) {
      console.error('Add member error:', error);
      return fail(500, { error: 'Failed to add member' });
    }
  },

  removeMember: async ({ request, locals, params }) => {
    if (!locals.user) {
      return fail(401, { error: 'Unauthorized' });
    }

    const projectId = parseInt(params.id);
    const formData = await request.formData();
    const memberId = parseInt(formData.get('member_id')?.toString() || '');

    if (isNaN(memberId)) {
      return fail(400, { error: 'Invalid member ID' });
    }

    try {
      const success = await projects.removeMember(projectId, locals.user.id, memberId);
      if (!success) {
        return fail(403, { error: 'Permission denied' });
      }

      return { success: true, message: 'Member removed successfully' };
    } catch (error) {
      console.error('Remove member error:', error);
      return fail(500, { error: 'Failed to remove member' });
    }
  }
};