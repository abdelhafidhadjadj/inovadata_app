import { error, fail, redirect } from '@sveltejs/kit';
import type { PageServerLoad, Actions } from './$types';
import { projects } from '$lib/server/projects';
import { datasets } from '$lib/server/datasets';

export const load: PageServerLoad = async ({ locals, params }) => {
  if (!locals.user) {
    throw redirect(303, '/login');
  }

  const projectId = parseInt(params.id);
  const datasetId = parseInt(params.datasetId);

  if (isNaN(projectId) || isNaN(datasetId)) {
    throw error(400, 'Invalid ID');
  }

  const [project, dataset] = await Promise.all([
    projects.getById(projectId, locals.user.id),
    datasets.getById(datasetId, locals.user.id)
  ]);

  if (!project) {
    throw error(404, 'Project not found');
  }

  if (!dataset) {
    throw error(404, 'Dataset not found');
  }

  // Verify dataset belongs to project
  if (dataset.project_id !== projectId) {
    throw error(404, 'Dataset not found in this project');
  }

  return {
    project,
    dataset
  };
};

export const actions: Actions = {
  delete: async ({ locals, params }) => {
    if (!locals.user) {
      return fail(401, { error: 'Unauthorized' });
    }

    const datasetId = parseInt(params.datasetId);
    const projectId = parseInt(params.id);

    try {
      const success = await datasets.delete(datasetId, locals.user.id);
      if (!success) {
        return fail(403, { error: 'Permission denied' });
      }

      throw redirect(303, `/dashboard/projects/${projectId}`);
    } catch (err) {
      if (err instanceof Response) throw err;
      console.error('Delete dataset error:', err);
      return fail(500, { error: 'Failed to delete dataset' });
    }
  },

  // NOUVEAU: Action pour retry
  retryProcessing: async ({ locals, params }) => {
    if (!locals.user) {
      return fail(401, { error: 'Unauthorized' });
    }

    const datasetId = parseInt(params.datasetId);

    try {
      const success = await datasets.retryProcessing(datasetId);
      if (!success) {
        return fail(404, { error: 'Dataset not found' });
      }

      return { success: true, message: 'Processing restarted' };
    } catch (err) {
      console.error('Retry processing error:', err);
      return fail(500, { error: 'Failed to retry processing' });
    }
  }
};