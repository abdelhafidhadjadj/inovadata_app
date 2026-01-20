import { error, fail, redirect } from '@sveltejs/kit';
import type { PageServerLoad, Actions } from './$types';
import { projects } from '$lib/server/projects';
import { datasets } from '$lib/server/datasets';
import { writeFile, mkdir } from 'fs/promises';
import { existsSync } from 'fs';
import path from 'path';

export const load: PageServerLoad = async ({ locals, params }) => {
  if (!locals.user) {
    throw redirect(303, '/login');
  }

  const projectId = parseInt(params.id);
  if (isNaN(projectId)) {
    throw error(400, 'Invalid project ID');
  }

  const project = await projects.getById(projectId, locals.user.id);
  if (!project) {
    throw error(404, 'Project not found');
  }

  // Check if user can upload (owner or editor)
  const hasPermission = await projects.hasPermission(projectId, locals.user.id, ['owner', 'editor']);
  if (!hasPermission) {
    throw error(403, 'You do not have permission to upload datasets to this project');
  }

  return {
    project
  };
};

export const actions: Actions = {
  upload: async ({ request, locals, params }) => {
    if (!locals.user) {
      return fail(401, { error: 'Unauthorized' });
    }

    const projectId = parseInt(params.id);
    const formData = await request.formData();
    
    const name = formData.get('name')?.toString();
    const description = formData.get('description')?.toString();
    const file = formData.get('file') as File;

    // Validation
    if (!name) {
      return fail(400, { error: 'Dataset name is required' });
    }

    if (!file || file.size === 0) {
      return fail(400, { error: 'Please select a file to upload' });
    }

    // Check file size (max 100MB)
    const maxSize = 100 * 1024 * 1024; // 100MB
    if (file.size > maxSize) {
      return fail(400, { error: 'File size must be less than 100MB' });
    }

    // Check file type
    const allowedTypes = ['.csv', '.json', '.arff'];
    const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!allowedTypes.includes(fileExtension)) {
      return fail(400, { 
        error: 'Invalid file type. Only CSV, JSON, and ARFF files are allowed',
        name,
        description
      });
    }

    // Define upload directory
    const uploadDir = path.join(process.cwd(), 'uploads', `project_${projectId}`);
    console.log('📁 Upload directory:', uploadDir);
    
    // Create directory if it doesn't exist
    if (!existsSync(uploadDir)) {
      console.log('📁 Creating directory...');
      try {
        await mkdir(uploadDir, { recursive: true });
      } catch (err) {
        console.error('❌ Failed to create directory:', err);
        return fail(500, { error: 'Failed to create upload directory' });
      }
    }

    // Generate unique filename
    const timestamp = Date.now();
    const sanitizedFilename = file.name.replace(/[^a-zA-Z0-9.-]/g, '_');
    const uniqueFilename = `${timestamp}_${sanitizedFilename}`;
    const filePath = path.join(uploadDir, uniqueFilename);
    
    console.log('📄 File will be saved to:', filePath);
    
    // Convert File to Buffer and save
    try {
      const arrayBuffer = await file.arrayBuffer();
      const buffer = Buffer.from(arrayBuffer);
      console.log('💾 Writing file, size:', buffer.length, 'bytes');
      await writeFile(filePath, buffer);
      console.log('✅ File written successfully');
    } catch (err) {
      console.error('❌ File write error:', err);
      return fail(500, { 
        error: 'Failed to save file. Please try again.',
        name,
        description
      });
    }

    // Create dataset record in database
    console.log('💾 Creating database record...');
    let dataset;
    try {
      dataset = await datasets.create(projectId, locals.user.id, {
        name,
        filename: file.name,
        file_path: filePath,
        file_format: fileExtension.replace('.', ''),
        file_size: file.size,
        rows_count: 0,
        columns_count: 0,
        metadata: {
          description,
          uploaded_at: new Date().toISOString(),
          original_filename: file.name,
          stored_filename: uniqueFilename
        }
      });

      if (!dataset) {
        console.error('❌ Failed to create dataset in database');
        return fail(500, { error: 'Failed to create dataset' });
      }

      console.log('✅ Dataset created with ID:', dataset.id);
    } catch (err) {
      console.error('❌ Database error:', err);
      return fail(500, { 
        error: 'Failed to create dataset record. Please try again.',
        name,
        description
      });
    }

    // SUCCESS - Redirect (OUTSIDE any try-catch)
    console.log('🔄 Redirecting to dataset details page...');
    throw redirect(303, `/dashboard/projects/${projectId}/datasets/${dataset.id}`);
  }
};