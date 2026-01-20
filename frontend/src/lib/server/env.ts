import { env } from '$env/dynamic/private';

function getEnv(key: string, defaultValue?: string): string {
  const value = env[key] || process.env[key] || defaultValue;
  if (!value) {
    throw new Error(`Environment variable ${key} is not set`);
  }
  return value;
}

// Database configuration
export const DB_USER = getEnv('DB_USER', 'inovadata');
export const DB_PASSWORD = getEnv('DB_PASSWORD', 'djkqsqsldhqkedeqzdfq');
export const DB_NAME = getEnv('DB_NAME', 'inovadata');
export const DB_HOST = getEnv('DB_HOST', 'postgres');
export const DB_PORT = getEnv('DB_PORT', '5432');

// Build DATABASE_URL from components
export const DATABASE_URL = `postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}`;

// Session configuration
export const SESSION_SECRET = getEnv('SESSION_SECRET', 'hdjksqhdfhsqjgfdsqjgbfj');

// Flask configuration
export const FLASK_ENV = getEnv('FLASK_ENV', 'production');
export const SECRET_KEY = getEnv('SECRET_KEY', 'your-super-secret-key-change-this-in-production');

// File upload configuration
export const MAX_FILE_SIZE = parseInt(getEnv('MAX_FILE_SIZE', '104857600'));
export const UPLOAD_FOLDER = getEnv('UPLOAD_FOLDER', '/app/uploads');

// Node environment
export const NODE_ENV = getEnv('NODE_ENV', 'production');