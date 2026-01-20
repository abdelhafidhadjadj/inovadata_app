import db from './db';

export interface Project {
  id: number;
  name: string;
  description: string | null;
  owner_id: number;
  is_public: boolean;
  created_at: Date;
  updated_at: Date;
  status: string;
  metadata: any;
  owner_username?: string;
  member_role?: string;
}

export interface ProjectMember {
  id: number;
  project_id: number;
  user_id: number;
  role: 'owner' | 'editor' | 'viewer';
  added_at: Date;
  username?: string;
  email?: string;
}

export const projects = {
  // Create project
  create: async (
    name: string,
    ownerId: number,
    description?: string,
    isPublic: boolean = false
  ): Promise<Project> => {
    return await db.transaction(async (client) => {
      // Create project
      const projectResult = await client.query(
        `INSERT INTO projects (name, description, owner_id, is_public)
         VALUES ($1, $2, $3, $4)
         RETURNING *`,
        [name, description || null, ownerId, isPublic]
      );

      const project = projectResult.rows[0];

      // Add owner as member
      await client.query(
        `INSERT INTO project_members (project_id, user_id, role)
         VALUES ($1, $2, 'owner')`,
        [project.id, ownerId]
      );

      // Log activity
      await client.query(
        `INSERT INTO activity_logs (user_id, project_id, action, resource_type, resource_id)
         VALUES ($1, $2, 'create', 'project', $3)`,
        [ownerId, project.id, project.id]
      );

      return project;
    });
  },

  // Get user projects
  getUserProjects: async (userId: number): Promise<Project[]> => {
    const result = await db.query(
      `SELECT p.*, u.username as owner_username, pm.role as member_role
       FROM projects p
       JOIN users u ON p.owner_id = u.id
       JOIN project_members pm ON p.id = pm.project_id
       WHERE pm.user_id = $1
       ORDER BY p.updated_at DESC`,
      [userId]
    );

    return result.rows;
  },

  // Get project by ID
  getById: async (projectId: number, userId: number): Promise<Project | null> => {
    const result = await db.query(
      `SELECT p.*, u.username as owner_username, pm.role as member_role
       FROM projects p
       JOIN users u ON p.owner_id = u.id
       LEFT JOIN project_members pm ON p.id = pm.project_id AND pm.user_id = $2
       WHERE p.id = $1 AND (p.is_public = true OR pm.user_id = $2)`,
      [projectId, userId]
    );

    return result.rows[0] || null;
  },

  // Update project
  update: async (
    projectId: number,
    userId: number,
    updates: Partial<Pick<Project, 'name' | 'description' | 'is_public' | 'status'>>
  ): Promise<Project | null> => {
    // Check permission
    const hasPermission = await projects.hasPermission(projectId, userId, ['owner', 'editor']);
    if (!hasPermission) return null;

    const fields: string[] = [];
    const values: any[] = [];
    let paramCount = 1;

    if (updates.name !== undefined) {
      fields.push(`name = $${paramCount++}`);
      values.push(updates.name);
    }
    if (updates.description !== undefined) {
      fields.push(`description = $${paramCount++}`);
      values.push(updates.description);
    }
    if (updates.is_public !== undefined) {
      fields.push(`is_public = $${paramCount++}`);
      values.push(updates.is_public);
    }
    if (updates.status !== undefined) {
      fields.push(`status = $${paramCount++}`);
      values.push(updates.status);
    }

    fields.push(`updated_at = NOW()`);
    values.push(projectId);

    const result = await db.query(
      `UPDATE projects 
       SET ${fields.join(', ')}
       WHERE id = $${paramCount}
       RETURNING *`,
      values
    );

    // Log activity
    await db.query(
      `INSERT INTO activity_logs (user_id, project_id, action, resource_type, resource_id)
       VALUES ($1, $2, 'update', 'project', $3)`,
      [userId, projectId, projectId]
    );

    return result.rows[0] || null;
  },

  // Delete project
  delete: async (projectId: number, userId: number): Promise<boolean> => {
    // Check if user is owner
    const hasPermission = await projects.hasPermission(projectId, userId, ['owner']);
    if (!hasPermission) return false;

    await db.query('DELETE FROM projects WHERE id = $1', [projectId]);
    return true;
  },

  // Check user permission
  hasPermission: async (
    projectId: number,
    userId: number,
    allowedRoles: string[]
  ): Promise<boolean> => {
    const result = await db.query(
      `SELECT role FROM project_members
       WHERE project_id = $1 AND user_id = $2`,
      [projectId, userId]
    );

    if (result.rows.length === 0) return false;
    return allowedRoles.includes(result.rows[0].role);
  },

  // Get project members
  getMembers: async (projectId: number): Promise<ProjectMember[]> => {
    const result = await db.query(
      `SELECT pm.*, u.username, u.email
       FROM project_members pm
       JOIN users u ON pm.user_id = u.id
       WHERE pm.project_id = $1
       ORDER BY pm.added_at`,
      [projectId]
    );

    return result.rows;
  },

  // Add member
  addMember: async (
    projectId: number,
    userId: number,
    newMemberEmail: string,
    role: 'editor' | 'viewer'
  ): Promise<ProjectMember | null> => {
    // Check if requester has permission
    const hasPermission = await projects.hasPermission(projectId, userId, ['owner', 'editor']);
    if (!hasPermission) return null;

    // Find new member by email
    const userResult = await db.query(
      'SELECT id FROM users WHERE email = $1',
      [newMemberEmail]
    );

    if (userResult.rows.length === 0) return null;
    const newMemberId = userResult.rows[0].id;

    // Add member
    try {
      const result = await db.query(
        `INSERT INTO project_members (project_id, user_id, role)
         VALUES ($1, $2, $3)
         RETURNING *`,
        [projectId, newMemberId, role]
      );

      // Log activity
      await db.query(
        `INSERT INTO activity_logs (user_id, project_id, action, resource_type, resource_id, details)
         VALUES ($1, $2, 'add_member', 'project', $3, $4)`,
        [userId, projectId, projectId, JSON.stringify({ new_member_id: newMemberId, role })]
      );

      return result.rows[0];
    } catch (error: any) {
      if (error.code === '23505') { // Unique violation
        return null;
      }
      throw error;
    }
  },

  // Update member role
  updateMemberRole: async (
    projectId: number,
    userId: number,
    memberId: number,
    newRole: 'editor' | 'viewer'
  ): Promise<boolean> => {
    // Only owner can update roles
    const hasPermission = await projects.hasPermission(projectId, userId, ['owner']);
    if (!hasPermission) return false;

    // Can't change owner role
    const memberResult = await db.query(
      'SELECT role FROM project_members WHERE project_id = $1 AND user_id = $2',
      [projectId, memberId]
    );

    if (memberResult.rows.length === 0 || memberResult.rows[0].role === 'owner') {
      return false;
    }

    await db.query(
      'UPDATE project_members SET role = $1 WHERE project_id = $2 AND user_id = $3',
      [newRole, projectId, memberId]
    );

    return true;
  },

  // Remove member
  removeMember: async (
    projectId: number,
    userId: number,
    memberId: number
  ): Promise<boolean> => {
    // Only owner can remove members
    const hasPermission = await projects.hasPermission(projectId, userId, ['owner']);
    if (!hasPermission) return false;

    // Can't remove owner
    const memberResult = await db.query(
      'SELECT role FROM project_members WHERE project_id = $1 AND user_id = $2',
      [projectId, memberId]
    );

    if (memberResult.rows.length === 0 || memberResult.rows[0].role === 'owner') {
      return false;
    }

    await db.query(
      'DELETE FROM project_members WHERE project_id = $1 AND user_id = $2',
      [projectId, memberId]
    );

    return true;
  }
};

export default projects;