// ABOUTME: Database service for managing all database operations
// ABOUTME: Provides methods for CRUD operations on projects, issues, and sprints

import { Pool, PoolClient } from 'pg';
import { v4 as uuidv4 } from 'uuid';

export interface Project {
  id: string;
  name: string;
  description?: string;
  slug: string;
  color: string;
  icon: string;
  is_active: boolean;
  created_at: Date;
  updated_at: Date;
}

export interface Issue {
  id: string;
  project_id: string;
  title: string;
  description?: string;
  status: 'backlog' | 'todo' | 'in_progress' | 'in_review' | 'done' | 'cancelled';
  priority: number;
  story_points?: number;
  estimated_hours?: number;
  actual_hours?: number;
  assignee?: string;
  labels: string[];
  branch_name?: string;
  worktree_path?: string;
  ai_complexity_score?: any;
  ai_estimation?: any;
  ai_review?: any;
  ai_tests_generated: boolean;
  ai_docs_generated: boolean;
  created_at: Date;
  updated_at: Date;
  completed_at?: Date;
}

export interface Sprint {
  id: string;
  project_id: string;
  name: string;
  goal?: string;
  duration_hours: 2 | 4 | 8 | 24;
  start_date?: Date;
  end_date?: Date;
  status: 'planned' | 'active' | 'completed' | 'cancelled';
  velocity?: number;
  created_at: Date;
  updated_at: Date;
}

export class DatabaseService {
  constructor(private pool: Pool) {}

  async initialize(): Promise<void> {
    const client = await this.pool.connect();
    try {
      await client.query('SELECT 1');
      console.log('Database connection verified');
    } finally {
      client.release();
    }
  }

  // Projects
  async createProject(data: Partial<Project>): Promise<Project> {
    const id = uuidv4();
    const slug = data.slug || data.name?.toLowerCase().replace(/\s+/g, '-');
    
    const query = `
      INSERT INTO projects (id, name, description, slug, color, icon)
      VALUES ($1, $2, $3, $4, $5, $6)
      RETURNING *
    `;
    
    const values = [
      id,
      data.name,
      data.description || null,
      slug,
      data.color || '#3B82F6',
      data.icon || 'folder'
    ];
    
    const result = await this.pool.query(query, values);
    return result.rows[0];
  }

  async getProjects(): Promise<Project[]> {
    const query = 'SELECT * FROM projects WHERE is_active = true ORDER BY created_at DESC';
    const result = await this.pool.query(query);
    return result.rows;
  }

  async getProjectById(id: string): Promise<Project | null> {
    const query = 'SELECT * FROM projects WHERE id = $1';
    const result = await this.pool.query(query, [id]);
    return result.rows[0] || null;
  }

  async updateProject(id: string, data: Partial<Project>): Promise<Project> {
    const fields = [];
    const values = [];
    let paramCount = 1;
    
    Object.entries(data).forEach(([key, value]) => {
      if (key !== 'id' && key !== 'created_at' && key !== 'updated_at') {
        fields.push(`${key} = $${paramCount}`);
        values.push(value);
        paramCount++;
      }
    });
    
    values.push(id);
    
    const query = `
      UPDATE projects 
      SET ${fields.join(', ')}
      WHERE id = $${paramCount}
      RETURNING *
    `;
    
    const result = await this.pool.query(query, values);
    return result.rows[0];
  }

  // Issues
  async createIssue(data: Partial<Issue>): Promise<Issue> {
    const id = uuidv4();
    
    const query = `
      INSERT INTO issues (
        id, project_id, title, description, status, priority, 
        story_points, estimated_hours, assignee, labels
      )
      VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
      RETURNING *
    `;
    
    const values = [
      id,
      data.project_id,
      data.title,
      data.description || null,
      data.status || 'backlog',
      data.priority || 3,
      data.story_points || null,
      data.estimated_hours || null,
      data.assignee || null,
      JSON.stringify(data.labels || [])
    ];
    
    const result = await this.pool.query(query, values);
    return result.rows[0];
  }

  async getIssues(projectId?: string): Promise<Issue[]> {
    let query = 'SELECT * FROM issues';
    const values: any[] = [];
    
    if (projectId) {
      query += ' WHERE project_id = $1';
      values.push(projectId);
    }
    
    query += ' ORDER BY created_at DESC';
    
    const result = await this.pool.query(query, values);
    return result.rows;
  }

  async getIssueById(id: string): Promise<Issue | null> {
    const query = 'SELECT * FROM issues WHERE id = $1';
    const result = await this.pool.query(query, [id]);
    return result.rows[0] || null;
  }

  async updateIssue(id: string, data: Partial<Issue>): Promise<Issue> {
    const fields = [];
    const values = [];
    let paramCount = 1;
    
    Object.entries(data).forEach(([key, value]) => {
      if (key !== 'id' && key !== 'created_at' && key !== 'updated_at') {
        if (key === 'labels' || key === 'ai_complexity_score' || key === 'ai_estimation' || key === 'ai_review') {
          fields.push(`${key} = $${paramCount}::jsonb`);
          values.push(JSON.stringify(value));
        } else {
          fields.push(`${key} = $${paramCount}`);
          values.push(value);
        }
        paramCount++;
      }
    });
    
    values.push(id);
    
    const query = `
      UPDATE issues 
      SET ${fields.join(', ')}
      WHERE id = $${paramCount}
      RETURNING *
    `;
    
    const result = await this.pool.query(query, values);
    return result.rows[0];
  }

  // Sprints
  async createSprint(data: Partial<Sprint>): Promise<Sprint> {
    const id = uuidv4();
    
    const query = `
      INSERT INTO sprints (
        id, project_id, name, goal, duration_hours, status
      )
      VALUES ($1, $2, $3, $4, $5, $6)
      RETURNING *
    `;
    
    const values = [
      id,
      data.project_id,
      data.name,
      data.goal || null,
      data.duration_hours,
      data.status || 'planned'
    ];
    
    const result = await this.pool.query(query, values);
    return result.rows[0];
  }

  async getSprints(projectId?: string): Promise<Sprint[]> {
    let query = 'SELECT * FROM sprints';
    const values: any[] = [];
    
    if (projectId) {
      query += ' WHERE project_id = $1';
      values.push(projectId);
    }
    
    query += ' ORDER BY created_at DESC';
    
    const result = await this.pool.query(query, values);
    return result.rows;
  }

  async getSprintById(id: string): Promise<Sprint | null> {
    const query = 'SELECT * FROM sprints WHERE id = $1';
    const result = await this.pool.query(query, [id]);
    return result.rows[0] || null;
  }

  async addIssuesToSprint(sprintId: string, issueIds: string[]): Promise<void> {
    const client = await this.pool.connect();
    try {
      await client.query('BEGIN');
      
      for (let i = 0; i < issueIds.length; i++) {
        await client.query(
          'INSERT INTO sprint_issues (sprint_id, issue_id, position) VALUES ($1, $2, $3)',
          [sprintId, issueIds[i], i]
        );
      }
      
      await client.query('COMMIT');
    } catch (error) {
      await client.query('ROLLBACK');
      throw error;
    } finally {
      client.release();
    }
  }

  async getSprintIssues(sprintId: string): Promise<Issue[]> {
    const query = `
      SELECT i.* 
      FROM issues i
      JOIN sprint_issues si ON i.id = si.issue_id
      WHERE si.sprint_id = $1
      ORDER BY si.position
    `;
    
    const result = await this.pool.query(query, [sprintId]);
    return result.rows;
  }

  // Activity logging
  async logActivity(entityType: string, entityId: string, action: string, metadata?: any): Promise<void> {
    const query = `
      INSERT INTO activity_log (id, entity_type, entity_id, action, metadata)
      VALUES ($1, $2, $3, $4, $5)
    `;
    
    const values = [
      uuidv4(),
      entityType,
      entityId,
      action,
      JSON.stringify(metadata || {})
    ];
    
    await this.pool.query(query, values);
  }
}