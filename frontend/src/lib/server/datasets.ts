import db from './db';
import { projects } from './projects';

export interface Dataset {
  id: number;
  project_id: number;
  name: string;
  filename: string | null;
  file_path: string | null;
  file_format: string | null;
  file_size: number | null;
  upload_date: Date;
  rows_count: number | null;
  columns_count: number | null;
  metadata: any;
  preprocessing_history: any;
  current_state: any;
  created_by: number;
  
  // Data Processing Service fields
  columns_info?: any;
  memory_usage?: number | null;
  processing_status?: string;
  processing_error?: string | null;
  processed_at?: Date | null;
  
  creator_username?: string;
}

export interface DatasetVersion {
  id: number;
  dataset_id: number;
  version_number: number;
  description: string | null;
  preprocessing_steps: any;
  created_at: Date;
  created_by: number;
}

export const datasets = {
  // Create dataset record
  create: async (
    projectId: number,
    userId: number,
    data: {
      name: string;
      filename?: string;
      file_path?: string;
      file_format?: string;
      file_size?: number;
      rows_count?: number;
      columns_count?: number;
      metadata?: any;
    }
  ): Promise<Dataset | null> => {
    // Check permission
    const hasPermission = await projects.hasPermission(projectId, userId, ['owner', 'editor']);
    if (!hasPermission) return null;

    const result = await db.query(
      `INSERT INTO datasets (
        project_id, name, filename, file_path, file_format, 
        file_size, rows_count, columns_count, metadata, created_by,
        processing_status
      )
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, 'pending')
      RETURNING *`,
      [
        projectId,
        data.name,
        data.filename || null,
        data.file_path || null,
        data.file_format || null,
        data.file_size || null,
        data.rows_count || 0,
        data.columns_count || 0,
        data.metadata ? JSON.stringify(data.metadata) : null,
        userId
      ]
    );

    const dataset = result.rows[0];

    // Log activity
    await db.query(
      `INSERT INTO activity_logs (user_id, project_id, action, resource_type, resource_id)
       VALUES ($1, $2, 'create', 'dataset', $3)`,
      [userId, projectId, dataset.id]
    );

    // Trigger async processing (don't wait for it)
    if (data.file_path && data.file_format) {
      datasets.processDatasetAsync(dataset.id, data.file_path, data.file_format)
        .catch(error => {
          console.error(`❌ Failed to process dataset ${dataset.id}:`, error);
        });
    }

    return dataset;
  },

  /**
   * Process dataset asynchronously using Data Processing Service
   */
  processDatasetAsync: async (
    datasetId: number,
    filePath: string,
    fileFormat: string
  ): Promise<void> => {
    try {
      console.log(`📊 Processing dataset ${datasetId}...`);

      // Update status to processing
      await db.query(
        `UPDATE datasets SET processing_status = 'processing' WHERE id = $1`,
        [datasetId]
      );

      // Call Data Processing Service
      const response = await fetch('http://data-processing:8001/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          dataset_id: datasetId,
          file_path: filePath,
          file_format: fileFormat,
          sample_size: 100
        })
      });

      if (!response.ok) {
        throw new Error(`Processing service error: ${response.statusText}`);
      }

      const analysis = await response.json();

      if (!analysis.success) {
        throw new Error(analysis.errors?.join(', ') || 'Processing failed');
      }

      // Update dataset with analysis results
      await db.query(
        `UPDATE datasets 
         SET rows_count = $1,
             columns_count = $2,
             columns_info = $3,
             memory_usage = $4,
             processing_status = 'completed',
             processed_at = NOW(),
             processing_error = NULL
         WHERE id = $5`,
        [
          analysis.rows_count,
          analysis.columns_count,
          JSON.stringify(analysis.columns),
          analysis.memory_usage,
          datasetId
        ]
      );

      console.log(`✅ Dataset ${datasetId} processed successfully`);
      console.log(`   Rows: ${analysis.rows_count}, Columns: ${analysis.columns_count}`);

    } catch (error) {
      console.error(`❌ Error processing dataset ${datasetId}:`, error);

      // Update status to failed
      await db.query(
        `UPDATE datasets 
         SET processing_status = 'failed',
             processing_error = $1
         WHERE id = $2`,
        [error instanceof Error ? error.message : 'Unknown error', datasetId]
      );
    }
  },

  /**
   * Retry processing for failed dataset
   */
  retryProcessing: async (datasetId: number): Promise<boolean> => {
    const result = await db.query(
      'SELECT file_path, file_format FROM datasets WHERE id = $1',
      [datasetId]
    );

    if (result.rows.length === 0) {
      return false;
    }

    const { file_path, file_format } = result.rows[0];

    if (!file_path || !file_format) {
      return false;
    }

    // Reset status and trigger processing again
    await db.query(
      `UPDATE datasets SET processing_status = 'pending', processing_error = NULL WHERE id = $1`,
      [datasetId]
    );

    datasets.processDatasetAsync(datasetId, file_path, file_format)
      .catch(error => {
        console.error(`Failed to retry processing for dataset ${datasetId}:`, error);
      });

    return true;
  },

  // Get project datasets
  getByProject: async (projectId: number, userId: number): Promise<Dataset[]> => {
    // Check permission
    const hasPermission = await projects.hasPermission(projectId, userId, ['owner', 'editor', 'viewer']);
    if (!hasPermission) return [];

    const result = await db.query(
      `SELECT d.*, u.username as creator_username
       FROM datasets d
       JOIN users u ON d.created_by = u.id
       WHERE d.project_id = $1
       ORDER BY d.upload_date DESC`,
      [projectId]
    );

    return result.rows;
  },

  // Get dataset by ID
  getById: async (datasetId: number, userId: number): Promise<Dataset | null> => {
    const result = await db.query(
      `SELECT d.*, u.username as creator_username
       FROM datasets d
       JOIN users u ON d.created_by = u.id
       WHERE d.id = $1`,
      [datasetId]
    );

    if (result.rows.length === 0) return null;

    const dataset = result.rows[0];

    // Check permission
    const hasPermission = await projects.hasPermission(
      dataset.project_id,
      userId,
      ['owner', 'editor', 'viewer']
    );

    return hasPermission ? dataset : null;
  },

  // Update dataset metadata
  updateMetadata: async (
    datasetId: number,
    userId: number,
    metadata: any
  ): Promise<Dataset | null> => {
    const dataset = await datasets.getById(datasetId, userId);
    if (!dataset) return null;

    const hasPermission = await projects.hasPermission(
      dataset.project_id,
      userId,
      ['owner', 'editor']
    );
    if (!hasPermission) return null;

    const result = await db.query(
      `UPDATE datasets 
       SET metadata = $1, current_state = $2
       WHERE id = $3
       RETURNING *`,
      [JSON.stringify(metadata), JSON.stringify(metadata), datasetId]
    );

    return result.rows[0];
  },

  // Update preprocessing history
  updatePreprocessing: async (
    datasetId: number,
    userId: number,
    preprocessingStep: any
  ): Promise<Dataset | null> => {
    const dataset = await datasets.getById(datasetId, userId);
    if (!dataset) return null;

    const hasPermission = await projects.hasPermission(
      dataset.project_id,
      userId,
      ['owner', 'editor']
    );
    if (!hasPermission) return null;

    const history = dataset.preprocessing_history || [];
    history.push({
      ...preprocessingStep,
      timestamp: new Date(),
      user_id: userId
    });

    const result = await db.query(
      `UPDATE datasets 
       SET preprocessing_history = $1
       WHERE id = $2
       RETURNING *`,
      [JSON.stringify(history), datasetId]
    );

    return result.rows[0];
  },

  // Delete dataset
  delete: async (datasetId: number, userId: number): Promise<boolean> => {
    const dataset = await datasets.getById(datasetId, userId);
    if (!dataset) return false;

    const hasPermission = await projects.hasPermission(
      dataset.project_id,
      userId,
      ['owner', 'editor']
    );
    if (!hasPermission) return false;

    await db.query('DELETE FROM datasets WHERE id = $1', [datasetId]);
    return true;
  },

  // Create version
  createVersion: async (
    datasetId: number,
    userId: number,
    description: string,
    preprocessingSteps: any
  ): Promise<DatasetVersion | null> => {
    const dataset = await datasets.getById(datasetId, userId);
    if (!dataset) return null;

    const hasPermission = await projects.hasPermission(
      dataset.project_id,
      userId,
      ['owner', 'editor']
    );
    if (!hasPermission) return null;

    // Get next version number
    const countResult = await db.query(
      'SELECT COUNT(*) as count FROM dataset_versions WHERE dataset_id = $1',
      [datasetId]
    );
    const versionNumber = parseInt(countResult.rows[0].count) + 1;

    const result = await db.query(
      `INSERT INTO dataset_versions (dataset_id, version_number, description, preprocessing_steps, created_by)
       VALUES ($1, $2, $3, $4, $5)
       RETURNING *`,
      [datasetId, versionNumber, description, JSON.stringify(preprocessingSteps), userId]
    );

    return result.rows[0];
  },

  // Get dataset versions
  getVersions: async (datasetId: number, userId: number): Promise<DatasetVersion[]> => {
    const dataset = await datasets.getById(datasetId, userId);
    if (!dataset) return [];

    const result = await db.query(
      `SELECT * FROM dataset_versions
       WHERE dataset_id = $1
       ORDER BY version_number DESC`,
      [datasetId]
    );

    return result.rows;
  }
};

export default datasets;