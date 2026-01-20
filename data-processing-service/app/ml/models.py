from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from enum import Enum
from datetime import datetime

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