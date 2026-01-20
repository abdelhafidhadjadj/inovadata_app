import { error, fail, redirect } from '@sveltejs/kit';
import type { PageServerLoad, Actions } from './$types';
import { projects } from '$lib/server/projects';
import { datasets } from '$lib/server/datasets';
import { db } from '$lib/server/db';

export const load: PageServerLoad = async ({ locals, params, url }) => {
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

  if (!project || !dataset) {
    throw error(404, 'Not found');
  }

  if (dataset.processing_status !== 'completed') {
    throw error(400, 'Dataset must be processed first');
  }

  const columnsInfo = typeof dataset.columns_info === 'string' 
    ? JSON.parse(dataset.columns_info) 
    : dataset.columns_info || [];

  const columnConfigs = columnsInfo.map((col: any) => {
    const minParam = url.searchParams.get(`${col.name}_min`);
    const maxParam = url.searchParams.get(`${col.name}_max`);
    const customMissing = url.searchParams.get(`${col.name}_missing`);

    return {
      name: col.name,
      custom_missing_values: customMissing ? customMissing.split(',').map(v => v.trim()) : ['?', '??', '-', '--', 'N/A', 'NA'],
      valid_range: (minParam || maxParam) ? {
        min: minParam ? parseFloat(minParam) : null,
        max: maxParam ? parseFloat(maxParam) : null
      } : null,
      detect_outliers: true
    };
  }).filter((config: any) => 
    config.valid_range || 
    (config.custom_missing_values && config.custom_missing_values.length > 0)
  );

  const customMissingParams = new Map<string, string>();
  for (const [key, value] of url.searchParams) {
    if (key.endsWith('_missing')) {
      const columnName = key.replace('_missing', '');
      customMissingParams.set(columnName, value);
    }
  }
  try {
    const response = await fetch('http://data-processing:8001/analyze-advanced', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        file_path: dataset.file_path,
        file_format: dataset.file_format,
        custom_missing_values: Array.from(customMissingParams.values()).flatMap(v => v.split(',')),
        column_configs: Array.from(customMissingParams.entries()).map(([name, values]) => ({
        name,
        custom_missing_values: values.split(',').map(v => v.trim())
      })),
        detect_outliers: true
      })
    });

    if (!response.ok) {
      throw new Error('Failed to get analysis');
    }

    let previewData = [];
    try {
      const previewResponse = await fetch('http://data-processing:8001/preview', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          file_path: dataset.file_path,
          file_format: dataset.file_format,
          limit: 1000, // Limiter à 1000 points pour performance
          offset: 0
        })
      });
      
      if (previewResponse.ok) {
        const previewResult = await previewResponse.json();
        previewData = previewResult.data;
      }
    } catch (err) {
      console.error('Failed to get preview data:', err);
    }

    const analysis = await response.json();

    return {
      project,
      dataset,
      analysis: analysis.columns,
      previewData 
    };
  } catch (err) {
    console.error('Analysis error:', err);
    throw error(500, 'Failed to analyze dataset');
  }
};

export const actions: Actions = {
  analyzeWithRanges: async ({ request, locals, params }) => {
    if (!locals.user) {
      return fail(401, { error: 'Unauthorized' });
    }
    return { success: true };
  },
  
  fillMissing: async ({ request, locals, params }) => {
  if (!locals.user) {
    return fail(401, { error: 'Unauthorized' });
  }

  const projectId = parseInt(params.id);
  const datasetId = parseInt(params.datasetId);
  const formData = await request.formData();
  const columnName = formData.get('column_name')?.toString();
  const action = formData.get('action')?.toString();
  const customMissing = formData.get('custom_missing')?.toString();
  const method = formData.get('method')?.toString();
  const replacementStrategy = formData.get('replacement_strategy')?.toString();
  const minValue = formData.get('min_value')?.toString();
  const maxValue = formData.get('max_value')?.toString();

  if (!columnName || !action) {
    return fail(400, { error: 'Column name and action required' });
  }

  try {
    const dataset = await datasets.getById(datasetId, locals.user.id);
    if (!dataset) {
      return fail(404, { error: 'Dataset not found' });
    }

    // CORRECTION: Nouvelle logique pour générer le nom de fichier
    const timestamp = Date.now();
    const originalPath = dataset.file_path!;
    
    // Extraire l'extension
    const lastDotIndex = originalPath.lastIndexOf('.');
    const extension = originalPath.substring(lastDotIndex); // .csv, .arff, .json
    
    // Extraire le chemin de base (sans l'extension)
    let basePath = originalPath.substring(0, lastDotIndex);
    
    // Si le fichier a déjà une version (_v{timestamp}), la supprimer
    const versionPattern = /_v\d+$/;
    if (versionPattern.test(basePath)) {
      basePath = basePath.replace(versionPattern, '');
    }
    
    // Créer le nouveau chemin
    const outputPath = `${basePath}_v${timestamp}${extension}`;

    console.log('Original path:', originalPath);
    console.log('Output path:', outputPath);

    // Construire la requête
    const requestBody: any = {
      file_path: originalPath,
      file_format: dataset.file_format,
      column_name: columnName,
      action: action,
      output_path: outputPath,
      custom_missing_values: customMissing ? customMissing.split(',').map(v => v.trim()) : null
    };

    if (action === 'replace_outliers' || action === 'remove_outliers') {
      requestBody.method = method || 'range';
      requestBody.replacement_strategy = replacementStrategy || 'mean';
      if (minValue) requestBody.min_value = parseFloat(minValue);
      if (maxValue) requestBody.max_value = parseFloat(maxValue);
    }

    // Preprocessing
    const preprocessResponse = await fetch('http://data-processing:8001/preprocess', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody)
    });

    if (!preprocessResponse.ok) {
      const errorData = await preprocessResponse.json();
      return fail(500, { error: errorData.detail || 'Preprocessing failed' });
    }

    const preprocessResult = await preprocessResponse.json();

    // Première mise à jour
    const updateResult1 = await db.query(
      `UPDATE datasets d
       SET file_path = $1,
           rows_count = $2,
           processing_status = 'pending',
           updated_at = NOW()
       FROM projects p
       WHERE d.id = $3 
         AND d.project_id = p.id
         AND p.owner_id = $4
       RETURNING d.*`,
      [outputPath, preprocessResult.final_rows, datasetId, locals.user.id]
    );

    if (updateResult1.rows.length === 0) {
      return fail(403, { error: 'Unauthorized to modify this dataset' });
    }

    // Re-traiter
    const processResponse = await fetch('http://data-processing:8001/process', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        dataset_id: datasetId,
        file_path: outputPath,
        file_format: dataset.file_format,
        sample_size: 100
      })
    });

    if (processResponse.ok) {
      const processResult = await processResponse.json();
      
      // Deuxième mise à jour
      await db.query(
        `UPDATE datasets d
         SET columns_info = $1,
             processing_status = 'completed',
             memory_usage = $2,
             updated_at = NOW()
         FROM projects p
         WHERE d.id = $3
           AND d.project_id = p.id
           AND p.owner_id = $4`,
        [
          JSON.stringify(processResult.columns),
          processResult.memory_usage,
          datasetId,
          locals.user.id
        ]
      );
    }

    return { 
      success: true, 
      message: `${preprocessResult.message}. Dataset updated.`,
      columnName: columnName
    };

  } catch (err) {
    console.error('Fill missing error:', err);
    return fail(500, { error: 'Failed to process data' });
  }
}
};