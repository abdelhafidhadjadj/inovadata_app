CREATE USER IF NOT EXISTS postgres WITH PASSWORD 'postgres' CREATEDB;

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    avatar_url VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE
);

-- Table Sessions (sessions en base, pas Redis)
CREATE TABLE sessions (
    id VARCHAR(255) PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    data JSONB,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Table Projects
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'active',
    metadata JSONB
);

-- Table Project Members (collaboration)
CREATE TABLE project_members (
    id SERIAL PRIMARY KEY,
    project_id INT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) DEFAULT 'viewer', -- owner, editor, viewer
    added_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(project_id, user_id),
    CONSTRAINT project_members_project_id_fkey 
    FOREIGN KEY (project_id) 
    REFERENCES projects(id) 
    ON DELETE CASCADE
);

-- Table Datasets
CREATE TABLE datasets (
    id SERIAL PRIMARY KEY,
    project_id INT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    filename VARCHAR(255),
    file_path VARCHAR(500),
    file_format VARCHAR(20), -- csv, json, arff
    file_size FLOAT,
    upload_date TIMESTAMP DEFAULT NOW(),
    rows_count INT,
    columns_count INT,
    columns_info JSONB DEFAULT '[]'::jsonb,
    memory_usage FLOAT,
    processing_status VARCHAR(50) DEFAULT 'pending',
    processing_error TEXT,
    metadata JSONB,
    preprocessing_history JSONB,
    current_state JSONB,
    processed_at TIMESTAMP,
    created_by INT NOT NULL REFERENCES users(id),
    UNIQUE(project_id, name),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT datasets_project_id_fkey 
    FOREIGN KEY (project_id) 
    REFERENCES projects(id) 
    ON DELETE CASCADE
);

-- Table Dataset Versions
CREATE TABLE dataset_versions (
    id SERIAL PRIMARY KEY,
    dataset_id INT NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    version_number INT,
    description VARCHAR(255),
    preprocessing_steps JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    transformations JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by INT NOT NULL REFERENCES users(id)
);

CREATE TABLE ml_experiments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    project_id INT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    dataset_id INT NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    transformations_path VARCHAR(500),
    roc_data JSONB,
    residuals JSONB,
    predictions JSONB,
    -- Configuration de l'algorithme
    algorithm VARCHAR(50) NOT NULL,
    hyperparameters JSONB DEFAULT '{}'::jsonb,
    
    -- Features et target
    target_column VARCHAR(100) NOT NULL,
    feature_columns JSONB NOT NULL,
    
    -- Configuration du split
    train_ratio FLOAT DEFAULT 0.8,
    random_seed INT DEFAULT 100,
    
    -- Résultats
    metrics JSONB,
    confusion_matrix JSONB,
    training_time FLOAT,
    
    -- Fichier modèle
    model_path VARCHAR(500),
    
    -- Statut
    status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    
    -- Audit
    created_by INT NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);


-- Table Visualizations
CREATE TABLE visualizations (
    id SERIAL PRIMARY KEY,
    dataset_id INT NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    name VARCHAR(255),
    chart_type VARCHAR(50),
    chart_config JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by INT NOT NULL REFERENCES users(id)
);

-- Table Activity Logs
CREATE TABLE activity_logs (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id),
    project_id INT REFERENCES projects(id),
    action VARCHAR(100),
    resource_type VARCHAR(50),
    resource_id INT,
    details JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT activity_logs_project_id_fkey 
    FOREIGN KEY (project_id) 
    REFERENCES projects(id) 
    ON DELETE CASCADE
);

-- Indices
CREATE INDEX idx_projects_owner ON projects(owner_id);
CREATE INDEX idx_datasets_project ON datasets(project_id);
CREATE INDEX idx_experiments_project ON ml_experiments(project_id);
CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_expires ON sessions(expires_at);
