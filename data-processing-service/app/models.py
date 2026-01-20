from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from enum import Enum
from datetime import datetime


class FileFormat(str, Enum):
    CSV = "csv"
    JSON = "json"
    ARFF = "arff"


class DataType(str, Enum):
    NUMERICAL = "numerical"
    CATEGORICAL = "categorical"
    TEXT = "text"
    DATETIME = "datetime"
    BOOLEAN = "boolean"


# NOUVEAU: Modèle pour définir un intervalle valide
class ColumnRange(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None


# NOUVEAU: Modèle pour configuration par colonne
class ColumnConfig(BaseModel):
    name: str
    custom_missing_values: Optional[List[str]] = None
    valid_range: Optional[ColumnRange] = None
    detect_outliers: bool = True


# NOUVEAU: Request amélioré pour analyse avancée
class AdvancedAnalysisRequest(BaseModel):
    file_path: str
    file_format: FileFormat
    
    # Global custom missing values (appliqué à toutes les colonnes)
    custom_missing_values: Optional[List[str]] = Field(default_factory=lambda: ['?', '??', '-', '--', 'N/A'])
    
    # Configuration spécifique par colonne
    column_configs: Optional[List[ColumnConfig]] = None
    
    # Colonnes à analyser (si None, toutes)
    columns: Optional[List[str]] = None
    
    # Détection d'outliers globale
    detect_outliers: bool = True


class ColumnInfo(BaseModel):
    name: str
    data_type: DataType
    missing_count: int
    missing_percentage: float
    unique_count: int
    sample_values: List[Any] = Field(default_factory=list)
    
    # For numerical columns
    mean: Optional[float] = None
    std: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None
    median: Optional[float] = None
    q25: Optional[float] = None
    q75: Optional[float] = None
    
    # For categorical columns
    top_values: Optional[Dict[str, int]] = None


class ProcessRequest(BaseModel):
    dataset_id: int
    file_path: str
    file_format: FileFormat
    sample_size: Optional[int] = 100


class ProcessResponse(BaseModel):
    dataset_id: int
    success: bool
    rows_count: int
    columns_count: int
    columns: List[ColumnInfo]
    preview_data: List[Dict[str, Any]]
    memory_usage: float
    processing_time: float
    errors: Optional[List[str]] = None


class DataPreviewRequest(BaseModel):
    file_path: str
    file_format: FileFormat
    limit: int = 100
    offset: int = 0


class DataPreviewResponse(BaseModel):
    data: List[Dict[str, Any]]
    total_rows: int
    columns: List[str]


class StatisticsRequest(BaseModel):
    file_path: str
    file_format: FileFormat
    columns: Optional[List[str]] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    supported_formats: List[str]





class ExperimentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    project_id: int
    dataset_id: int
    algorithm: str  # 'knn', 'decision_tree', etc.
    hyperparameters: Dict = {}
    target_column: str
    feature_columns: List[str]
    train_ratio: float = 0.8
    random_seed: int = 42

class ExperimentResponse(BaseModel):
    id: int
    name: str
    algorithm: str
    status: str
    metrics: Optional[Dict] = None
    confusion_matrix: Optional[Dict] = None
    training_time: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True