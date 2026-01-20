import pg from 'pg';
import { env } from '$env/dynamic/private';

const { Pool } = pg;

// Construire DATABASE_URL à partir des variables d'environnement
const DB_USER = env.DB_USER || 'inovadata';
const DB_PASSWORD = env.DB_PASSWORD || 'djkqsqsldhqkedeqzdfq';
const DB_NAME = env.DB_NAME || 'inovadata';
const DB_HOST = env.DB_HOST || 'postgres';
const DB_PORT = env.DB_PORT || '5432';

const DATABASE_URL = `postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}`;

const pool = new Pool({
  connectionString: DATABASE_URL,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

pool.on('error', (err) => {
  console.error('Unexpected database error:', err);
});

export const db = {
  query: async (text: string, params?: any[]) => {
    const start = Date.now();
    try {
      const result = await pool.query(text, params);
      const duration = Date.now() - start;
      
      // Log seulement en mode debug (optionnel)
      if (process.env.DEBUG === 'true') {
        console.log('Executed query', { text, duration, rows: result.rowCount });
      }
      
      return result;
    } catch (error) {
      console.error('Database query error:', error);
      throw error;
    }
  },

  getClient: async () => {
    return await pool.connect();
  },

  transaction: async <T>(callback: (client: pg.PoolClient) => Promise<T>): Promise<T> => {
    const client = await pool.connect();
    try {
      await client.query('BEGIN');
      const result = await callback(client);
      await client.query('COMMIT');
      return result;
    } catch (error) {
      await client.query('ROLLBACK');
      throw error;
    } finally {
      client.release();
    }
  }
};

export default db;