CREATE USER postgres WITH PASSWORD 'postgres' CREATEDB;


--@block
SELECT * FROM users

--@block
SELECT * FROM projects

--@block
SELECT * FROM datasets

--@block
SELECT * FROM dataset_versions
--@block
UPDATE users SET is_admin = 'TRUE' WHERE id = 1



--@block

ALTER TABLE dataset_versions 
ADD COLUMN IF NOT EXISTS file_path VARCHAR(500);

-- Ajouter la colonne is_active
--@block
ALTER TABLE dataset_versions 
ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;


--@block
-- Add columns_info to store detailed column analysis from the processing service
ALTER TABLE datasets ADD COLUMN updated_at TIMESTAMP DEFAULT NOW();

--@block

ALTER TABLE dataset_versions
ADD COLUMN IF NOT EXISTS transformations JSONB;
--@block

ALTER TABLE datasets 
ADD COLUMN IF NOT EXISTS columns_info JSONB DEFAULT '[]'::jsonb;

-- Add memory_usage to track dataset size in memory
ALTER TABLE datasets 
ADD COLUMN IF NOT EXISTS memory_usage FLOAT;

-- Add processing_status to track analysis state
ALTER TABLE datasets 
ADD COLUMN IF NOT EXISTS processing_status VARCHAR(50) DEFAULT 'pending';
-- Values: pending, processing, completed, failed

-- Add processing_error for debugging
ALTER TABLE datasets 
ADD COLUMN IF NOT EXISTS processing_error TEXT;

-- Add processed_at timestamp
ALTER TABLE datasets 
ADD COLUMN IF NOT EXISTS processed_at TIMESTAMP;

-- Add index for faster queries
CREATE INDEX IF NOT EXISTS idx_datasets_processing_status ON datasets(processing_status);

-- Comment on columns
COMMENT ON COLUMN datasets.columns_info IS 'Detailed analysis of each column (types, statistics, missing values) from Data Processing Service';
COMMENT ON COLUMN datasets.memory_usage IS 'Memory usage in MB calculated by Data Processing Service';
COMMENT ON COLUMN datasets.processing_status IS 'Status of data processing: pending, processing, completed, failed';
COMMENT ON COLUMN datasets.processing_error IS 'Error message if processing failed';
COMMENT ON COLUMN datasets.processed_at IS 'Timestamp when data processing was completed';

--@block
SELECT * FROM dataset_versions

--@block
DELETE FROM datasets WHERE id='13';




--@block
DROP TABLE  ml_experiments CASCADE;


--@block
ALTER TABLE ml_experiments 
ADD COLUMN IF NOT EXISTS roc_data JSONB,
ADD COLUMN IF NOT EXISTS residuals JSONB,
ADD COLUMN IF NOT EXISTS predictions JSONB;
--@block
-- Table pour les expériences ML
CREATE TABLE ml_experiments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    project_id INT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    dataset_id INT NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    
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

CREATE INDEX idx_ml_experiments_dataset ON ml_experiments(dataset_id);
CREATE INDEX idx_ml_experiments_status ON ml_experiments(status);
