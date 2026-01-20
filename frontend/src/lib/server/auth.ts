import bcrypt from 'bcrypt';
import { db } from './db';
import crypto from 'crypto';

export const auth = {
  async validateSession(sessionId: string) {
    const result = await db.query(
      `SELECT u.id, u.username, u.email, u.full_name, u.avatar_url, u.is_active, u.is_admin, u.created_at
       FROM sessions s
       JOIN users u ON s.user_id = u.id
       WHERE s.id = $1 AND s.expires_at > NOW() AND u.is_active = true`,
      [sessionId]
    );

    if (result.rows.length === 0) {
      return null;
    }

    return result.rows[0];
  },

  async createSession(userId: number) {
    const sessionId = crypto.randomBytes(32).toString('hex');
    const expiresAt = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000); // 7 days

    await db.query(
      `INSERT INTO sessions (id, user_id, expires_at)
       VALUES ($1, $2, $3)`,
      [sessionId, userId, expiresAt]
    );

    return sessionId;
  },

  async deleteSession(sessionId: string) {
    await db.query('DELETE FROM sessions WHERE id = $1', [sessionId]);
  },

  async findUser(usernameOrEmail: string) {
    const result = await db.query(
      `SELECT id, username, email, full_name, avatar_url, is_active, is_admin, created_at
       FROM users
       WHERE username = $1 OR email = $1`,
      [usernameOrEmail]
    );
    return result.rows[0] || null;
  },

  async createUser(username: string, email: string, password: string, fullName?: string) {
    const passwordHash = await bcrypt.hash(password, 10);
    
    const result = await db.query(
      `INSERT INTO users (username, email, password_hash, full_name)
       VALUES ($1, $2, $3, $4)
       RETURNING id, username, email, full_name, avatar_url, is_active, is_admin, created_at`,
      [username, email, passwordHash, fullName]
    );

    return result.rows[0];
  },

  async verifyPassword(password: string, hash: string) {
    return await bcrypt.compare(password, hash);
  }
};