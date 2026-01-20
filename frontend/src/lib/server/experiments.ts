import db from './db';
import { projects } from './projects';

export interface Experiment {
  id: number;
  project_id: number;
  dataset_id: number;
  name: string | null;
  model_type: string;
  algorithm: string;
  hyperparameters: any;
  training_config: any;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  training_time_seconds: number | null;
  created_at: Date;
  completed_at: Date | null;
  created_by: number;
  dataset_name?: string;
  creator_username?: string;
}

export interface ExperimentResult {
  id: number;
  experiment_id: number;
  metrics: any;
  confusion_matrix: any;
  feature_importance: any;
  train_metrics: any;
  test_metrics: any;
  validation_metrics: any;
  model_artifact_path: string | null;
  created_at: Date;
}

export const experiments = {
  // Create experiment
  create: async (
    projectId: number,
    datasetId: number,
    userId: number,
    config: {
      name?: string;
      model_type: string;
      algorithm: string;
      hyperparameters?: any;
      training_config?: any;
    }
  ): Promise<Experiment | null> => {
    // Check permission
    const hasPermission = await projects.hasPermission(projectId, userId, ['owner', 'editor']);
    if (!hasPermission) return null;

    const result = await db.query(
      `INSERT INTO experiments (
        project_id, dataset_id, name, model_type, algorithm,
        hyperparameters, training_config, created_by
      )
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
      RETURNING *`,
      [
        projectId,
        datasetId,
        config.name || null,
        config.model_type,
        config.algorithm,
        config.hyperparameters ? JSON.stringify(config.hyperparameters) : null,
        config.training_config ? JSON.stringify(config.training_config) : null,
        userId
      ]
    );

    // Log activity
    await db.query(
      `INSERT INTO activity_logs (user_id, project_id, action, resource_type, resource_id)
       VALUES ($1, $2, 'create', 'experiment', $3)`,
      [userId, projectId, result.rows[0].id]
    );

    return result.rows[0];
  },

  // Get project experiments
  getByProject: async (projectId: number, userId: number): Promise<Experiment[]> => {
    // Check permission
    const hasPermission = await projects.hasPermission(projectId, userId, ['owner', 'editor', 'viewer']);
    if (!hasPermission) return [];

    const result = await db.query(
      `SELECT e.*, d.name as dataset_name, u.username as creator_username
       FROM experiments e
       JOIN datasets d ON e.dataset_id = d.id
       JOIN users u ON e.created_by = u.id
       WHERE e.project_id = $1
       ORDER BY e.created_at DESC`,
      [projectId]
    );

    return result.rows;
  },

  // Get experiment by ID
  getById: async (experimentId: number, userId: number): Promise<Experiment | null> => {
    const result = await db.query(
      `SELECT e.*, d.name as dataset_name, u.username as creator_username
       FROM experiments e
       JOIN datasets d ON e.dataset_id = d.id
       JOIN users u ON e.created_by = u.id
       WHERE e.id = $1`,
      [experimentId]
    );

    if (result.rows.length === 0) return null;

    const experiment = result.rows[0];
    
    // Check permission
    const hasPermission = await projects.hasPermission(
      experiment.project_id,
      userId,
      ['owner', 'editor', 'viewer']
    );
    
    return hasPermission ? experiment : null;
  },

  // Update experiment status
  updateStatus: async (
    experimentId: number,
    status: 'pending' | 'running' | 'completed' | 'failed',
    progress?: number
  ): Promise<Experiment | null> => {
    const updates: string[] = ['status = $1'];
    const values: any[] = [status];
    let paramCount = 2;

    if (progress !== undefined) {
      updates.push(`progress = $${paramCount++}`);
      values.push(progress);
    }

    if (status === 'completed' || status === 'failed') {
      updates.push(`completed_at = NOW()`);
    }

    values.push(experimentId);

    const result = await db.query(
      `UPDATE experiments 
       SET ${updates.join(', ')}
       WHERE id = $${paramCount}
       RETURNING *`,
      values
    );

    return result.rows[0] || null;
  },

  // Update training time
  updateTrainingTime: async (
    experimentId: number,
    trainingTimeSeconds: number
  ): Promise<void> => {
    await db.query(
      'UPDATE experiments SET training_time_seconds = $1 WHERE id = $2',
      [trainingTimeSeconds, experimentId]
    );
  },

  // Save experiment results
  saveResults: async (
    experimentId: number,
    results: {
      metrics?: any;
      confusion_matrix?: any;
      feature_importance?: any;
      train_metrics?: any;
      test_metrics?: any;
      validation_metrics?: any;
      model_artifact_path?: string;
    }
  ): Promise<ExperimentResult> => {
    const result = await db.query(
      `INSERT INTO experiment_results (
        experiment_id, metrics, confusion_matrix, feature_importance,
        train_metrics, test_metrics, validation_metrics, model_artifact_path
      )
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
      RETURNING *`,
      [
        experimentId,
        results.metrics ? JSON.stringify(results.metrics) : null,
        results.confusion_matrix ? JSON.stringify(results.confusion_matrix) : null,
        results.feature_importance ? JSON.stringify(results.feature_importance) : null,
        results.train_metrics ? JSON.stringify(results.train_metrics) : null,
        results.test_metrics ? JSON.stringify(results.test_metrics) : null,
        results.validation_metrics ? JSON.stringify(results.validation_metrics) : null,
        results.model_artifact_path || null
      ]
    );

    return result.rows[0];
  },

  // Get experiment results
  getResults: async (experimentId: number, userId: number): Promise<ExperimentResult | null> => {
    const experiment = await experiments.getById(experimentId, userId);
    if (!experiment) return null;

    const result = await db.query(
      'SELECT * FROM experiment_results WHERE experiment_id = $1',
      [experimentId]
    );

    return result.rows[0] || null;
  },

  // Delete experiment
  delete: async (experimentId: number, userId: number): Promise<boolean> => {
    const experiment = await experiments.getById(experimentId, userId);
    if (!experiment) return false;

    const hasPermission = await projects.hasPermission(
      experiment.project_id,
      userId,
      ['owner', 'editor']
    );
    if (!hasPermission) return false;

    await db.query('DELETE FROM experiments WHERE id = $1', [experimentId]);
    return true;
  },

  // Compare experiments
  compare: async (
    experimentIds: number[],
    userId: number
  ): Promise<Array<Experiment & { results?: ExperimentResult }>> => {
    if (experimentIds.length === 0) return [];

    const placeholders = experimentIds.map((_, i) => `$${i + 1}`).join(',');
    
    const result = await db.query(
      `SELECT e.*, d.name as dataset_name, u.username as creator_username,
              er.metrics, er.train_metrics, er.test_metrics, er.validation_metrics
       FROM experiments e
       JOIN datasets d ON e.dataset_id = d.id
       JOIN users u ON e.created_by = u.id
       LEFT JOIN experiment_results er ON e.id = er.experiment_id
       WHERE e.id IN (${placeholders})`,
      experimentIds
    );

    // Filter by permission
    const experiments = [];
    for (const exp of result.rows) {
      const hasPermission = await projects.hasPermission(
        exp.project_id,
        userId,
        ['owner', 'editor', 'viewer']
      );
      if (hasPermission) {
        const { metrics, train_metrics, test_metrics, validation_metrics, ...experiment } = exp;
        experiments.push({
          ...experiment,
          results: metrics ? {
            metrics,
            train_metrics,
            test_metrics,
            validation_metrics
          } : undefined
        });
      }
    }

    return experiments;
  }
};

export default experiments;