import { error, redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';
import { projects } from '$lib/server/projects';
import { datasets } from '$lib/server/datasets';

export const load: PageServerLoad = async ({ locals, params, url }) => {
  if (!locals.user) {
    throw redirect(303, '/login');
  }

  const projectId = parseInt(params.id);
  const datasetId = parseInt(params.datasetId);
  const page = parseInt(url.searchParams.get('page') || '1');
  const limit = 50;
  const offset = (page - 1) * limit;

  if (isNaN(projectId) || isNaN(datasetId)) {
    throw error(400, 'Invalid ID');
  }

  const [project, dataset] = await Promise.all([
    projects.getById(projectId, locals.user.id),
    datasets.getById(datasetId, locals.user.id)
  ]);

  if (!project || !dataset) {
    throw error(404, 'Not found');
  }

  // Verify dataset is processed
  if (dataset.processing_status !== 'completed') {
    throw error(400, 'Dataset is not yet processed');
  }

  // Get preview data from Data Processing Service
  try {
    const response = await fetch('http://data-processing:8001/preview', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        file_path: dataset.file_path,
        file_format: dataset.file_format,
        limit,
        offset
      })
    });

    if (!response.ok) {
      throw new Error('Failed to get preview');
    }

    const preview = await response.json();

    return {
      project,
      dataset,
      preview: preview.data,
      columns: preview.columns,
      totalRows: preview.total_rows,
      currentPage: page,
      totalPages: Math.ceil(preview.total_rows / limit),
      limit
    };
  } catch (err) {
    console.error('Preview error:', err);
    throw error(500, 'Failed to load data preview');
  }
};