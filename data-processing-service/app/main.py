from fastapi import FastAPI, HTTPException, File, Form
from fastapi.middleware.cors import CORSMiddleware
import time
import logging
from typing import Dict, Any
import sys
import pandas as pd  
import numpy as np
from pydantic import BaseModel
from typing import List, Optional, Literal
from .models import (
    ProcessRequest, ProcessResponse, 
    DataPreviewRequest, DataPreviewResponse,
    StatisticsRequest, HealthResponse,
    FileFormat, AdvancedAnalysisRequest
)
from app.ml.preprocessor import DataPreprocessor

import joblib
import os
import psycopg2
from .preprocessing.transformers import DataTransformer
from sklearn.tree import export_graphviz
import graphviz
import matplotlib.pyplot as plt
import io
import base64
import json
from .processors import CSVProcessor, JSONProcessor, ARFFProcessor
from .utils import clean_records_for_json, clean_value_for_json
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Data Processing Service",
    description="Microservice for processing and analyzing datasets",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Processor mapping
PROCESSORS = {
    FileFormat.CSV: CSVProcessor,
    FileFormat.JSON: JSONProcessor,
    FileFormat.ARFF: ARFFProcessor
}
def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'postgres'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'inovadata'),
        user=os.getenv('DB_USER', 'inovadata'),
        password=os.getenv('DB_PASSWORD', 'djkqsqsldhqkedeqzdfq')
    )

def load_dataset(file_path: str, file_format: str) -> pd.DataFrame:
    """Load dataset from file with automatic CSV fallback for ARFF"""
    import os
    
    try:
        # ✅ Si le fichier n'existe pas
        if not os.path.exists(file_path):
            logger.warning(f"⚠️ File not found: {file_path}")
            
            # Si ARFF, essayer avec .csv
            if file_format == 'arff' or file_path.endswith('.arff'):
                csv_path = file_path.replace('.arff', '.csv')
                
                if os.path.exists(csv_path):
                    logger.info(f"✅ ARFF not found, using CSV: {csv_path}")
                    file_path = csv_path
                    file_format = 'csv'
                else:
                    raise FileNotFoundError(f"Neither ARFF nor CSV found for: {file_path}")
        
        # Charger selon le format
        if file_format == 'csv':
            return pd.read_csv(file_path)
        elif file_format == 'json':
            return pd.read_json(file_path)
        elif file_format == 'arff':
            from app.processors.arff_processor import ARFFProcessor
            return ARFFProcessor.read(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_format}")
            
    except Exception as e:
        logger.error(f"❌ Error loading dataset: {str(e)}")
        raise

def save_dataset(df: pd.DataFrame, file_path: str, file_format: str):
    """Save dataset to file"""
    if file_format == 'csv':
        df.to_csv(file_path, index=False)
    elif file_format == 'json':
        df.to_json(file_path, orient='records', indent=2)
    elif file_format == 'arff':
        from scipy.io import arff
        # Implementation for ARFF
        pass
    else:
        raise ValueError(f"Unsupported file format: {file_format}")

def create_dataset_version(
    db,
    dataset_id: int,
    file_path: str,
    description: str,
    transformations: list
):
    """Create a new dataset version in database"""
    
    # Get current max version number
    cursor = db.cursor()
    cursor.execute(
        "SELECT COALESCE(MAX(version_number), 0) FROM dataset_versions WHERE dataset_id = %s",
        (dataset_id,)
    )
    max_version = cursor.fetchone()[0]
    new_version = max_version + 1
    
    # Deactivate previous active version
    cursor.execute(
        "UPDATE dataset_versions SET is_active = FALSE WHERE dataset_id = %s AND is_active = TRUE",
        (dataset_id,)
    )
    
    # Insert new version
    cursor.execute(
        """
        INSERT INTO dataset_versions (dataset_id, version_number, file_path, description, transformations, is_active)
        VALUES (%s, %s, %s, %s, %s, TRUE)
        RETURNING id
        """,
        (dataset_id, new_version, file_path, description, json.dumps(transformations))
    )
    
    version_id = cursor.fetchone()[0]
    db.commit()
    cursor.close()
    
    return version_id, new_version


@app.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        supported_formats=["csv", "json", "arff"]
    )


@app.post("/process", response_model=ProcessResponse)
async def process_dataset(request: ProcessRequest):
    """Process a dataset file and extract metadata"""
    start_time = time.time()
    errors = []
    columns_info = []
    
    try:
        logger.info(f"Processing dataset {request.dataset_id} at {request.file_path}")
        
        # ✅ Vérifier si le fichier existe, sinon essayer CSV
        import os
        file_path = request.file_path
        file_format = request.file_format
        
        if not os.path.exists(file_path):
            if file_format == FileFormat.ARFF or file_path.endswith('.arff'):
                csv_path = file_path.replace('.arff', '.csv')
                if os.path.exists(csv_path):
                    logger.info(f"⚠️ ARFF not found, using CSV: {csv_path}")
                    file_path = csv_path
                    file_format = FileFormat.CSV
        
        # Get appropriate processor
        processor_class = PROCESSORS.get(file_format)
        if not processor_class:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file format: {file_format}"
            )
        
        # Read file
        try:
            processor = processor_class()
            df = processor.read(file_path)
            logger.info(f"Successfully read file: {len(df)} rows, {len(df.columns)} columns")
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="File not found")
        except Exception as e:
            logger.error(f"Error reading file: {e}")
            raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")
        
        # Analyze columns (toujours utiliser CSVProcessor)
        try:
            columns_info = CSVProcessor.analyze_dataframe(df)
            logger.info(f"Analyzed {len(columns_info)} columns")
        except Exception as e:
            logger.error(f"Error analyzing columns: {e}")
            errors.append(f"Column analysis error: {str(e)}")
            columns_info = []
        
        # Get preview data
        try:
            preview_df = df.head(request.sample_size)
            records = preview_df.to_dict('records')
            preview_data = clean_records_for_json(records)
        except Exception as e:
            logger.error(f"Error creating preview: {e}")
            errors.append(f"Preview generation error: {str(e)}")
            preview_data = []
        
        # Calculate memory usage
        memory_usage = df.memory_usage(deep=True).sum() / (1024 * 1024)
        
        processing_time = time.time() - start_time
        
        logger.info(f"Processing completed in {processing_time:.2f}s")
        
        return ProcessResponse(
            dataset_id=request.dataset_id,
            success=len(errors) == 0,
            rows_count=len(df),
            columns_count=len(df.columns),
            columns=columns_info,
            preview_data=preview_data,
            memory_usage=round(memory_usage, 2),
            processing_time=round(processing_time, 2),
            errors=errors if errors else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing dataset: {e}")
        raise HTTPException(status_code=500, detail=str(e))    

@app.post("/preview", response_model=DataPreviewResponse)
async def get_data_preview(request: DataPreviewRequest):
    """
    Get paginated preview of dataset
    
    Useful for displaying data tables with pagination
    """
    try:
        logger.info(f"Getting preview for {request.file_path} (limit={request.limit}, offset={request.offset})")
        
        # Get appropriate processor
        processor = PROCESSORS.get(request.file_format)
        if not processor:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file format: {request.file_format}"
            )
        
        # Get preview data
        data, total_rows, columns = processor.get_preview(
            request.file_path,
            limit=request.limit,
            offset=request.offset
        )
        
        return DataPreviewResponse(
            data=data,
            total_rows=total_rows,
            columns=columns
        )
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error(f"Error getting preview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/statistics")
async def get_statistics(request: StatisticsRequest):
    """
    Get detailed statistics for specific columns
    
    Returns comprehensive statistical analysis
    """
    try:
        logger.info(f"Getting statistics for {request.file_path}")
        
        # Get appropriate processor
        processor = PROCESSORS.get(request.file_format)
        if not processor:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file format: {request.file_format}"
            )
        
        # Read file
        df = processor.read(request.file_path)
        
        # Filter columns if specified
        if request.columns:
            df = df[request.columns]
        
        # Analyze
        columns_info = processor.analyze_dataframe(df)
        
        return {
            "columns": [col.dict() for col in columns_info],
            "total_rows": len(df),
            "total_columns": len(df.columns)
        }
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))



@app.post("/analyze-advanced")
async def analyze_advanced(request: AdvancedAnalysisRequest):
    """Advanced analysis with automatic CSV fallback"""
    start_time = time.time()
    
    try:
        logger.info(f"Advanced analysis for {request.file_path}")
        
        # ✅ Vérifier si le fichier existe, sinon essayer CSV
        import os
        file_path = request.file_path
        file_format = request.file_format
        
        if not os.path.exists(file_path):
            if file_format == FileFormat.ARFF or file_path.endswith('.arff'):
                csv_path = file_path.replace('.arff', '.csv')
                if os.path.exists(csv_path):
                    logger.info(f"⚠️ ARFF not found, using CSV: {csv_path}")
                    file_path = csv_path
                    file_format = FileFormat.CSV
        
        # Get processor
        processor_class = PROCESSORS.get(file_format)
        if not processor_class:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported format: {file_format}"
            )
        
        # ✅ Instancier le processor
        processor = processor_class()
        
        # Read file
        df = processor.read(file_path)
        
        logger.info(f"Dataset loaded: {len(df)} rows, {len(df.columns)} columns")
        
        # Filter columns if specified
        if request.columns:
            df = df[request.columns]
        
        # Build column config map for easy lookup
        column_config_map = {}
        if request.column_configs:
            for config in request.column_configs:
                column_config_map[config.name] = config
        
        # Analyze each column
        results = []
        for column in df.columns:
            # Get config for this column (or use defaults)
            col_config = column_config_map.get(column)
            
            # Determine custom missing values for this column
            custom_missing = request.custom_missing_values or []
            if col_config and col_config.custom_missing_values:
                custom_missing = col_config.custom_missing_values
            
            # Determine if outlier detection is enabled
            detect_outliers_flag = request.detect_outliers
            if col_config is not None:
                detect_outliers_flag = col_config.detect_outliers
            
            # Analyze column
            analysis = CSVProcessor.analyze_column_advanced(
                df[column],
                column,
                custom_missing,
                detect_outliers_flag
            )
            
            # Add range validation if specified
            if col_config and col_config.valid_range:
                valid_range = col_config.valid_range
                range_info = CSVProcessor.detect_outliers_range(
                    df[column],
                    min_val=valid_range.min,
                    max_val=valid_range.max
                )
                
                if 'outliers' not in analysis:
                    analysis['outliers'] = {}
                analysis['outliers']['range'] = range_info
                
                # Add configured range to response
                analysis['configured_range'] = {
                    'min': valid_range.min,
                    'max': valid_range.max
                }
            
            results.append(analysis)
        
        processing_time = time.time() - start_time
        
        return {
            'success': True,
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'columns': results,
            'processing_time': round(processing_time, 2)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Advanced analysis error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    

class PreprocessRequest(BaseModel):
    file_path: str
    file_format: FileFormat
    column_name: str
    action: Literal['fill_mean', 'fill_median', 'fill_mode', 'fill_forward', 'remove_rows', 'remove_outliers', 'replace_outliers']
    custom_missing_values: Optional[List[str]] = None
    output_path: Optional[str] = None
    
    # Pour remove/replace outliers
    method: Optional[Literal['iqr', 'zscore', 'range']] = 'iqr'
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    replacement_strategy: Optional[Literal['mean', 'median', 'mode']] = 'mean'

@app.post("/preprocess")
async def preprocess_data(request: PreprocessRequest):
    """Apply preprocessing action to a column"""
    try:
        logger.info(f"Preprocessing {request.column_name} with action: {request.action}")
        
        # ✅ CORRECTION 1 : Vérifier si le fichier existe, sinon essayer CSV
        import os
        file_path = request.file_path
        file_format = request.file_format
        
        if not os.path.exists(file_path):
            if file_format == FileFormat.ARFF or file_path.endswith('.arff'):
                csv_path = file_path.replace('.arff', '.csv')
                if os.path.exists(csv_path):
                    logger.info(f"⚠️ ARFF not found, using CSV: {csv_path}")
                    file_path = csv_path
                    file_format = FileFormat.CSV
                else:
                    raise HTTPException(
                        status_code=404, 
                        detail=f"File not found: {file_path} (tried CSV alternative too)"
                    )
        
        # Get processor
        processor_class = PROCESSORS.get(file_format)
        if not processor_class:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {file_format}")
        
        # ✅ CORRECTION 2 : Instancier le processor
        processor = processor_class()
        
        # Read file
        df = processor.read(file_path)
        original_rows = len(df)
        
        # Detect custom missing values if provided
        if request.custom_missing_values and request.action in ['fill_mean', 'fill_median', 'fill_mode', 'fill_forward', 'remove_rows']:
            custom_missing_mask = CSVProcessor.detect_custom_missing_values(
                df[request.column_name],
                request.custom_missing_values
            )
            df.loc[custom_missing_mask, request.column_name] = pd.NA
        
        # Apply the action (votre code existant...)
        if request.action == 'fill_mean':
            if not pd.api.types.is_numeric_dtype(df[request.column_name]):
                raise HTTPException(status_code=400, detail="Mean fill only works with numerical columns")
            mean_value = df[request.column_name].mean()
            filled_count = df[request.column_name].isna().sum()
            df[request.column_name].fillna(mean_value, inplace=True)
            result_message = f"Filled {filled_count} missing values with mean: {mean_value:.2f}"
            
        elif request.action == 'fill_median':
            if not pd.api.types.is_numeric_dtype(df[request.column_name]):
                raise HTTPException(status_code=400, detail="Median fill only works with numerical columns")
            median_value = df[request.column_name].median()
            filled_count = df[request.column_name].isna().sum()
            df[request.column_name].fillna(median_value, inplace=True)
            result_message = f"Filled {filled_count} missing values with median: {median_value:.2f}"
            
        elif request.action == 'fill_mode':
            mode_value = df[request.column_name].mode()
            if len(mode_value) > 0:
                filled_count = df[request.column_name].isna().sum()
                df[request.column_name].fillna(mode_value[0], inplace=True)
                result_message = f"Filled {filled_count} missing values with mode: {mode_value[0]}"
            else:
                result_message = "No mode found"
                
        elif request.action == 'fill_forward':
            filled_count = df[request.column_name].isna().sum()
            df[request.column_name].fillna(method='ffill', inplace=True)
            result_message = f"Forward filled {filled_count} missing values"
            
        elif request.action == 'remove_rows':
            df = df.dropna(subset=[request.column_name])
            result_message = f"Removed {original_rows - len(df)} rows with missing values"
        
        elif request.action == 'replace_outliers':
            method = request.method
            replacement_strategy = request.replacement_strategy

            outlier_mask = pd.Series([False] * len(df), index=df.index)

            if method == 'range':
                if request.min_value is not None:
                    outlier_mask |= df[request.column_name] < request.min_value
                if request.max_value is not None:
                    outlier_mask |= df[request.column_name] > request.max_value

            elif method == 'iqr':
                Q1 = df[request.column_name].quantile(0.25)
                Q3 = df[request.column_name].quantile(0.75)
                IQR = Q3 - Q1
                lower = Q1 - 1.5 * IQR
                upper = Q3 + 1.5 * IQR
                outlier_mask = (df[request.column_name] < lower) | (df[request.column_name] > upper)

            elif method == 'zscore':
                mean = df[request.column_name].mean()
                std = df[request.column_name].std()
                if std > 0:
                    z_scores = np.abs((df[request.column_name] - mean) / std)
                    outlier_mask = z_scores > 3

            outlier_count = int(outlier_mask.sum())

            if outlier_count > 0:
                clean_values = df.loc[~outlier_mask, request.column_name]

                if replacement_strategy == 'mean':
                    replacement_value = clean_values.mean()
                    result_message = f"Replaced {outlier_count} outliers with mean: {replacement_value:.2f}"
                elif replacement_strategy == 'median':
                    replacement_value = clean_values.median()
                    result_message = f"Replaced {outlier_count} outliers with median: {replacement_value:.2f}"
                elif replacement_strategy == 'mode':
                    mode_values = clean_values.mode()
                    if len(mode_values) > 0:
                        replacement_value = mode_values[0]
                        result_message = f"Replaced {outlier_count} outliers with mode: {replacement_value}"
                    else:
                        replacement_value = clean_values.median()
                        result_message = f"Replaced {outlier_count} outliers with median (no mode found): {replacement_value:.2f}"
                elif replacement_strategy == 'min':
                    replacement_value = clean_values.min()
                    result_message = f"Replaced {outlier_count} outliers with min: {replacement_value:.2f}"
                elif replacement_strategy == 'max':
                    replacement_value = clean_values.max()
                    result_message = f"Replaced {outlier_count} outliers with max: {replacement_value:.2f}"

                original_dtype = df[request.column_name].dtype

                if pd.api.types.is_integer_dtype(original_dtype):
                    replacement_value_int = int(round(replacement_value))
                    df.loc[outlier_mask, request.column_name] = replacement_value_int
                    logger.info(f"Replaced {outlier_count} int values with {replacement_value_int}")
                else:
                    df[request.column_name] = df[request.column_name].astype(float)
                    df.loc[outlier_mask, request.column_name] = float(replacement_value)
                    logger.info(f"Replaced {outlier_count} float values with {replacement_value}")
            else:
                outlier_count = 0
                result_message = "No outliers detected"

            values_replaced = outlier_count
        
        elif request.action == 'remove_outliers':
            method = request.method
            before = len(df)
            
            if method == 'range':
                if request.min_value is not None:
                    df = df[df[request.column_name] >= request.min_value]
                if request.max_value is not None:
                    df = df[df[request.column_name] <= request.max_value]
                removed = before - len(df)
                result_message = f"Removed {removed} rows with outliers outside range [{request.min_value}, {request.max_value}]"
                
            elif method == 'iqr':
                Q1 = df[request.column_name].quantile(0.25)
                Q3 = df[request.column_name].quantile(0.75)
                IQR = Q3 - Q1
                lower = Q1 - 1.5 * IQR
                upper = Q3 + 1.5 * IQR
                df = df[(df[request.column_name] >= lower) & (df[request.column_name] <= upper)]
                removed = before - len(df)
                result_message = f"Removed {removed} rows with outliers using IQR method"
                
            elif method == 'zscore':
                mean = df[request.column_name].mean()
                std = df[request.column_name].std()
                z_scores = np.abs((df[request.column_name] - mean) / std)
                df = df[z_scores < 3]
                removed = before - len(df)
                result_message = f"Removed {removed} rows with outliers using Z-score method"
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown action: {request.action}")
        
        # ✅ CORRECTION 3 : Sauvegarder en CSV si c'était ARFF
        output_path = request.output_path or file_path
        original_format = request.file_format
        save_format = file_format  # Utiliser le format détecté, pas le format original

        # Si le format original était ARFF, forcer CSV
        if original_format == FileFormat.ARFF:
            output_path = output_path.replace('.arff', '.csv')
            save_format = FileFormat.CSV
            logger.info(f"⚠️ Converting ARFF to CSV: {output_path}")

        try:
            if save_format == FileFormat.CSV:
                df.to_csv(output_path, index=False)
                logger.info(f"✅ Saved CSV to {output_path}")
            elif save_format == FileFormat.JSON:
                df.to_json(output_path, orient='records')
                logger.info(f"✅ Saved JSON to {output_path}")
            else:
                # Fallback
                output_path = output_path.replace('.arff', '.csv')
                df.to_csv(output_path, index=False)
                save_format = FileFormat.CSV
                logger.info(f"✅ Saved as CSV to {output_path}")
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

        # ✅ CORRECTION 4 : Mettre à jour la DB si converti
        if original_format == FileFormat.ARFF and save_format == FileFormat.CSV:
            try:
                db = get_db_connection()
                cursor = db.cursor()
                
                cursor.execute(
                    "SELECT id FROM datasets WHERE file_path = %s",
                    (request.file_path,)
                )
                result = cursor.fetchone()
                
                if result:
                    dataset_id = result[0]
                    
                    cursor.execute(
                        """
                        UPDATE datasets 
                        SET file_path = %s, 
                            file_format = %s, 
                            updated_at = NOW() 
                        WHERE id = %s
                        """,
                        (output_path, 'csv', dataset_id)
                    )
                    db.commit()
                    logger.info(f"✅ Updated dataset {dataset_id}: ARFF → CSV")
                
                cursor.close()
                db.close()
                
            except Exception as db_error:
                logger.warning(f"⚠️ Could not update database: {db_error}")

        logger.info(f"Preprocessing complete: {result_message}")

        if 'values_replaced' not in locals():
            values_replaced = 0

        return {
            'success': True,
            'message': result_message,
            'original_rows': original_rows,
            'final_rows': len(df),
            'rows_affected': original_rows - len(df) if request.action in ['remove_outliers', 'remove_rows'] else 0,
            'values_replaced': values_replaced,
            'file_path': output_path,
            'file_format': save_format.value if hasattr(save_format, 'value') else str(save_format)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Preprocessing error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transform-preview-normalize")
async def preview_normalize(
    file_path: str = Form(...),
    file_format: str = Form(...),
    columns: str = Form(...),
    method: str = Form(...)
):
    """Preview normalization without applying"""
    try:
        columns_list = json.loads(columns)
        
        df = load_dataset(file_path, file_format)
        transformer = DataTransformer(df)
        
        preview = transformer.preview_normalization(columns_list, method)
        
        return preview
    
    except Exception as e:
        print(f"❌ Preview normalize error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transform-normalize")
async def transform_normalize(
    file_path: str = Form(...),
    file_format: str = Form(...),
    columns: str = Form(...),
    method: str = Form(...),
    feature_range_min: float = Form(0.0),
    feature_range_max: float = Form(1.0),
    dataset_id: int = Form(...),
    create_new_version: bool = Form(True)
):
    """Apply normalization to specified columns"""
    try:
        print(f"📊 Normalize request: {method} on {columns}")
        
        columns_list = json.loads(columns)
        
        # Charger le dataset
        df = load_dataset(file_path, file_format)
        print(f"✅ Dataset loaded: {len(df)} rows")
        
        # Appliquer la normalisation
        transformer = DataTransformer(df)
        feature_range = (feature_range_min, feature_range_max)
        transformed_df, info = transformer.normalize_columns(
            columns_list, 
            method, 
            feature_range
        )
        
        print(f"✅ Normalization completed")
        
        if create_new_version:
            import os
            from datetime import datetime
            
            base_dir = os.path.dirname(file_path)
            filename = os.path.basename(file_path)
            name, ext = os.path.splitext(filename)
            
            if '_v' in name:
                name = name.split('_v')[0]
            
            timestamp = int(datetime.now().timestamp() * 1000)
            
            # ✅ CORRECTION : Toujours sauvegarder en CSV après transformation
            new_filename = f"{name}_v{timestamp}.csv"
            new_file_path = os.path.join(base_dir, new_filename)
            new_format = 'csv'
            
            # Sauvegarder en CSV
            transformed_df.to_csv(new_file_path, index=False)
            print(f"✅ New version saved to CSV: {new_file_path}")
            
            try:
                db = get_db_connection()
                cursor = db.cursor()
                
                cursor.execute(
                    "SELECT created_by FROM datasets WHERE id = %s",
                    (dataset_id,)
                )
                result = cursor.fetchone()
                if not result:
                    raise Exception(f"Dataset {dataset_id} not found")
                
                created_by = result[0]
                
                cursor.execute(
                    "SELECT COALESCE(MAX(version_number), 0) FROM dataset_versions WHERE dataset_id = %s",
                    (dataset_id,)
                )
                max_version = cursor.fetchone()[0]
                new_version_number = max_version + 1
                
                description = f"Normalization: {method} on {', '.join(columns_list)}"
                
                cursor.execute(
                    "UPDATE dataset_versions SET is_active = FALSE WHERE dataset_id = %s",
                    (dataset_id,)
                )
                
                cursor.execute(
                    """
                    INSERT INTO dataset_versions 
                        (dataset_id, version_number, file_path, description, transformations, created_by, is_active)
                    VALUES 
                        (%s, %s, %s, %s, %s, %s, TRUE)
                    RETURNING id
                    """,
                    (
                        dataset_id,
                        new_version_number,
                        new_file_path,
                        description,
                        json.dumps([info]),
                        created_by
                    )
                )
                
                version_id = cursor.fetchone()[0]
                db.commit()
                
                # ✅ IMPORTANT : Mettre à jour le file_path ET le file_format
                cursor.execute(
                    """
                    UPDATE datasets 
                    SET file_path = %s, 
                        file_format = %s, 
                        updated_at = NOW() 
                    WHERE id = %s
                    """,
                    (new_file_path, new_format, dataset_id)
                )
                db.commit()
                
                cursor.close()
                db.close()
                
                return {
                    "success": True,
                    "message": f"Created version {new_version_number} with {method} normalization (saved as CSV)",
                    "version_id": version_id,
                    "version_number": new_version_number,
                    "file_path": new_file_path,
                    "file_format": new_format,  # ✅ Retourner le nouveau format
                    "transformation_info": info
                }
                
            except Exception as db_error:
                print(f"❌ Database error: {str(db_error)}")
                if os.path.exists(new_file_path):
                    os.remove(new_file_path)
                raise
        
        else:
            # Mode overwrite
            save_dataset(transformed_df, file_path, file_format)
            print(f"✅ Dataset overwritten")
            
            return {
                "success": True,
                "message": f"Successfully normalized {len(columns_list)} columns using {method}",
                "transformation_info": info
            }
    
    except Exception as e:
        print(f"❌ Transform normalize error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    

@app.post("/transform-preview-encode")
async def preview_encode(
    file_path: str = Form(...),
    file_format: str = Form(...),
    columns: str = Form(...),
    method: str = Form(...)
):
    """Preview encoding without applying"""
    try:
        columns_list = json.loads(columns)
        
        df = load_dataset(file_path, file_format)
        transformer = DataTransformer(df)
        
        preview = transformer.preview_encoding(columns_list, method)
        
        return preview
    
    except Exception as e:
        print(f"❌ Preview encode error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/transform-encode")
async def transform_encode(
    file_path: str = Form(...),
    file_format: str = Form(...),
    columns: str = Form(...),
    method: str = Form(...),
    drop_first: bool = Form(False),
    dataset_id: int = Form(...),
    create_new_version: bool = Form(True),
    created_by: int = Form(None)  # ✅ Déjà optionnel
):
    """Apply encoding to specified columns"""
    try:
        print(f"📊 Encode request: {method} on {columns}")
        print(f"📋 Parameters received:")
        print(f"  - file_path: {file_path}")
        print(f"  - file_format: {file_format}")
        print(f"  - columns: {columns}")
        print(f"  - method: {method}")
        print(f"  - drop_first: {drop_first}")
        print(f"  - dataset_id: {dataset_id}")
        print(f"  - create_new_version: {create_new_version}")
        print(f"  - created_by: {created_by}")
        
        columns_list = json.loads(columns)
        
        # ✅ Vérifier si le fichier existe, sinon essayer CSV
        import os
        actual_file_path = file_path
        actual_file_format = file_format
        
        if not os.path.exists(file_path):
            if file_format == 'arff' or file_path.endswith('.arff'):
                csv_path = file_path.replace('.arff', '.csv')
                if os.path.exists(csv_path):
                    print(f"⚠️ ARFF not found, using CSV: {csv_path}")
                    actual_file_path = csv_path
                    actual_file_format = 'csv'
        
        df = load_dataset(actual_file_path, actual_file_format)
        print(f"✅ Dataset loaded: {len(df)} rows")
        
        transformer = DataTransformer(df)
        transformed_df, info = transformer.encode_columns(
            columns_list,
            method,
            drop_first
        )
        
        print(f"✅ Encoding completed")
        
        if create_new_version:
            from datetime import datetime
            
            base_dir = os.path.dirname(actual_file_path)
            filename = os.path.basename(actual_file_path)
            name, ext = os.path.splitext(filename)
            
            if '_v' in name:
                name = name.split('_v')[0]
            
            timestamp = int(datetime.now().timestamp() * 1000)
            
            # ✅ Toujours sauvegarder en CSV
            new_filename = f"{name}_v{timestamp}.csv"
            new_file_path = os.path.join(base_dir, new_filename)
            new_format = 'csv'
            
            transformed_df.to_csv(new_file_path, index=False)
            print(f"✅ New version saved to CSV: {new_file_path}")
            
            try:
                db = get_db_connection()
                cursor = db.cursor()
                
                # ✅ Récupérer created_by depuis la DB si non fourni
                cursor.execute(
                    "SELECT created_by FROM datasets WHERE id = %s",
                    (dataset_id,)
                )
                result = cursor.fetchone()
                if not result:
                    raise Exception(f"Dataset {dataset_id} not found")
                
                db_created_by = result[0]
                final_created_by = created_by if created_by is not None else db_created_by
                
                cursor.execute(
                    "SELECT COALESCE(MAX(version_number), 0) FROM dataset_versions WHERE dataset_id = %s",
                    (dataset_id,)
                )
                max_version = cursor.fetchone()[0]
                new_version_number = max_version + 1
                
                description = f"Encoding: {method} on {', '.join(columns_list)}"
                if drop_first:
                    description += " (drop_first=True)"
                
                cursor.execute(
                    "UPDATE dataset_versions SET is_active = FALSE WHERE dataset_id = %s",
                    (dataset_id,)
                )
                
                cursor.execute(
                    """
                    INSERT INTO dataset_versions 
                        (dataset_id, version_number, file_path, description, transformations, created_by, is_active)
                    VALUES 
                        (%s, %s, %s, %s, %s, %s, TRUE)
                    RETURNING id
                    """,
                    (
                        dataset_id,
                        new_version_number,
                        new_file_path,
                        description,
                        json.dumps([info]),
                        final_created_by
                    )
                )
                
                version_id = cursor.fetchone()[0]
                db.commit()
                
                # ✅ Mettre à jour file_path ET file_format
                cursor.execute(
                    """
                    UPDATE datasets 
                    SET file_path = %s, 
                        file_format = %s, 
                        updated_at = NOW() 
                    WHERE id = %s
                    """,
                    (new_file_path, new_format, dataset_id)
                )
                db.commit()
                
                cursor.close()
                db.close()
                
                print(f"✅ Created version {new_version_number}")
                
                return {
                    "success": True,
                    "message": f"Created version {new_version_number} with {method} encoding (saved as CSV)",
                    "version_id": version_id,
                    "version_number": new_version_number,
                    "file_path": new_file_path,
                    "file_format": new_format,
                    "encoding_info": info
                }
                
            except Exception as db_error:
                print(f"❌ Database error: {str(db_error)}")
                import traceback
                traceback.print_exc()
                if os.path.exists(new_file_path):
                    os.remove(new_file_path)
                raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")
        
        else:
            # Mode overwrite
            if actual_file_format == 'csv' or file_format == 'arff':
                # Toujours sauvegarder en CSV
                csv_path = actual_file_path.replace('.arff', '.csv')
                transformed_df.to_csv(csv_path, index=False)
                print(f"✅ Dataset saved to CSV: {csv_path}")
            else:
                save_dataset(transformed_df, actual_file_path, actual_file_format)
                print(f"✅ Dataset overwritten")
            
            return {
                "success": True,
                "message": f"Successfully encoded {len(columns_list)} columns using {method}",
                "encoding_info": info
            }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Transform encode error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/datasets/{dataset_id}")
async def get_dataset(dataset_id: int):
    """Récupérer les informations d'un dataset"""
    db = get_db_connection()
    cursor = db.cursor()
    
    try:
        cursor.execute("""
            SELECT id, name, filename, file_path, file_format, file_size,
                   rows_count, columns_count, columns_info, processing_status,
                   upload_date
            FROM datasets
            WHERE id = %s
        """, (dataset_id,))
        
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Dataset non trouvé")
        
        # Parse columns_info si c'est une string JSON
        columns_info = result[8]
        if isinstance(columns_info, str):
            columns_info = json.loads(columns_info)
        
        return {
            'id': result[0],
            'name': result[1],
            'filename': result[2],
            'file_path': result[3],
            'file_format': result[4],
            'file_size': result[5],
            'rows_count': result[6],
            'columns_count': result[7],
            'columns_info': columns_info,
            'processing_status': result[9],
            'upload_date': result[10]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur récupération dataset: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()

@app.get("/dataset-versions/{dataset_id}")
async def get_dataset_versions(dataset_id: int):
    """Get all versions of a dataset"""
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute(
            """
            SELECT id, version_number, file_path, description, transformations, 
                   created_at, is_active
            FROM dataset_versions
            WHERE dataset_id = %s
            ORDER BY version_number DESC
            """,
            (dataset_id,)
        )
        
        versions = []
        for row in cursor.fetchall():
            versions.append({
                'id': row[0],
                'version_number': row[1],
                'file_path': row[2],
                'description': row[3],
                'transformations': row[4],
                'created_at': row[5].isoformat(),
                'is_active': row[6]
            })
        
        cursor.close()
        db.close()
        
        return versions
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# NOUVEAU : Endpoint pour activer une version
@app.post("/activate-version/{version_id}")
async def activate_version(version_id: int):
    """Set a specific version as active"""
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        # Get dataset_id from version
        cursor.execute(
            "SELECT dataset_id FROM dataset_versions WHERE id = %s",
            (version_id,)
        )
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Version not found")
        
        dataset_id = result[0]
        
        # Deactivate all versions
        cursor.execute(
            "UPDATE dataset_versions SET is_active = FALSE WHERE dataset_id = %s",
            (dataset_id,)
        )
        
        # Activate selected version
        cursor.execute(
            "UPDATE dataset_versions SET is_active = TRUE WHERE id = %s",
            (version_id,)
        )
        
        db.commit()
        cursor.close()
        db.close()
        
        return {"success": True, "message": "Version activated"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



from app.models import ExperimentCreate, ExperimentResponse
from app.ml.trainer import MLTrainer
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json

# Créer un executor pour les tâches longues
executor = ThreadPoolExecutor(max_workers=2)

# ============================================
# ROUTES ML
# ============================================

@app.post("/ml/experiments/create")
async def create_experiment(experiment: ExperimentCreate):
    """Créer une nouvelle expérience ML"""
    db = get_db_connection()
    cursor = db.cursor()
    
    try:
        # Vérifier que le dataset existe
        cursor.execute("""
            SELECT id, columns_info FROM datasets WHERE id = %s
        """, (experiment.dataset_id,))
        
        dataset = cursor.fetchone()
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset non trouvé")
        
        # Vérifier que les colonnes existent
        columns_info = dataset[1] or []
        available_columns = [col['name'] for col in columns_info]
        
        # Vérifier target
        if experiment.target_column not in available_columns:
            raise HTTPException(
                status_code=400, 
                detail=f"Colonne target '{experiment.target_column}' n'existe pas"
            )
        
        # Vérifier features
        missing_features = set(experiment.feature_columns) - set(available_columns)
        if missing_features:
            raise HTTPException(
                status_code=400,
                detail=f"Colonnes features manquantes: {missing_features}"
            )
        
        # Créer l'expérience en base
        cursor.execute("""
            INSERT INTO ml_experiments (
                name, description, project_id, dataset_id,
                algorithm, hyperparameters, target_column, feature_columns,
                train_ratio, random_seed, status, created_by
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending', %s
            ) RETURNING id, name, algorithm, status, created_at
        """, (
            experiment.name,
            experiment.description,
            experiment.project_id,
            experiment.dataset_id,
            experiment.algorithm,
            json.dumps(experiment.hyperparameters),
            experiment.target_column,
            json.dumps(experiment.feature_columns),
            experiment.train_ratio,
            experiment.random_seed,
            1  # TODO: Récupérer l'user_id depuis la session
        ))
        
        result = cursor.fetchone()
        db.commit()
        
        return {
            'id': result[0],
            'name': result[1],
            'algorithm': result[2],
            'status': result[3],
            'created_at': result[4]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Erreur création expérience: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


@app.post("/ml/experiments/{experiment_id}/train")
async def train_experiment(experiment_id: int):
    """Lancer l'entraînement d'une expérience"""
    db = get_db_connection()
    cursor = db.cursor()
    
    try:
        # Récupérer l'expérience
        cursor.execute("""
            SELECT e.id, e.dataset_id, e.project_id, e.algorithm, 
                   e.hyperparameters, e.target_column, e.feature_columns,
                   e.train_ratio, e.random_seed, e.status,
                   d.file_path
            FROM ml_experiments e
            JOIN datasets d ON d.id = e.dataset_id
            WHERE e.id = %s
        """, (experiment_id,))
        
        exp_result = cursor.fetchone()
        
        if not exp_result:
            raise HTTPException(status_code=404, detail="Expérience non trouvée")
        
        # Vérifier le statut
        if exp_result[9] == 'training':
            raise HTTPException(status_code=400, detail="Expérience déjà en cours")
        
        if exp_result[9] == 'completed':
            raise HTTPException(status_code=400, detail="Expérience déjà terminée")
        
        # Mettre à jour le statut
        cursor.execute("""
            UPDATE ml_experiments 
            SET status = 'training'
            WHERE id = %s
        """, (experiment_id,))
        db.commit()
        
        # Préparer la config pour le trainer
        config = {
            'algorithm': exp_result[3],
            'hyperparameters': exp_result[4] if isinstance(exp_result[4], dict) else json.loads(exp_result[4]) if exp_result[4] else {},
            'target_column': exp_result[5],
            'feature_columns': exp_result[6] if isinstance(exp_result[6], list) else json.loads(exp_result[6]),
            'train_ratio': float(exp_result[7]),
            'random_seed': int(exp_result[8])
        }
        
        dataset_path = exp_result[10]
        project_id = exp_result[2]
        
        # Lancer l'entraînement en arrière-plan
        loop = asyncio.get_event_loop()
        loop.run_in_executor(
            executor,
            train_in_background,
            experiment_id,
            project_id,
            dataset_path,
            config
        )
        
        return {
            'message': 'Entraînement démarré',
            'experiment_id': experiment_id,
            'status': 'training'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur démarrage entraînement: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


def train_in_background(experiment_id: int, project_id: int, dataset_path: str, config: dict):
    """Fonction qui s'exécute en arrière-plan pour l'entraînement"""
    
    db = get_db_connection()
    cursor = db.cursor()
    
    try:
        # Créer le trainer
        trainer = MLTrainer(dataset_path, config)
        
        # Exécuter l'entraînement
        results = trainer.run(experiment_id, project_id)
        
        # ✅ FIX : Nettoyer les valeurs Infinity/NaN dans les résultats JSON
        def clean_for_json(obj):
            """Remplace Infinity et NaN par None pour le JSON"""
            import math
            if isinstance(obj, dict):
                return {k: clean_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_for_json(item) for item in obj]
            elif isinstance(obj, float):
                if math.isinf(obj) or math.isnan(obj):
                    return None
                return obj
            return obj
        
        # Mettre à jour en base
        if results['status'] == 'completed':
            # Nettoyer les données avant insertion
            metrics = clean_for_json(results['metrics'])
            confusion_matrix = clean_for_json(results.get('confusion_matrix'))
            roc_data = clean_for_json(results.get('roc_data'))
            residuals = clean_for_json(results.get('residuals'))
            predictions = clean_for_json(results.get('predictions'))
            
            cursor.execute("""
                UPDATE ml_experiments
                SET status = 'completed',
                    metrics = %s,
                    confusion_matrix = %s,
                    roc_data = %s,
                    residuals = %s,
                    predictions = %s,
                    training_time = %s,
                    model_path = %s,
                    transformations_path = %s,
                    completed_at = NOW()
                WHERE id = %s
            """, (
                json.dumps(metrics) if metrics else None,
                json.dumps(confusion_matrix) if confusion_matrix else None,
                json.dumps(roc_data) if roc_data else None,
                json.dumps(residuals) if residuals else None,
                json.dumps(predictions) if predictions else None,
                results['training_time'],
                results['model_path'],
                results.get('transformations_path'),
                experiment_id
            ))
        else:
            cursor.execute("""
                UPDATE ml_experiments
                SET status = 'failed',
                    error_message = %s
                WHERE id = %s
            """, (
                results.get('error_message', 'Unknown error'),
                experiment_id
            ))
        
        db.commit()
        logger.info(f"Expérience {experiment_id} terminée: {results['status']}")
        
    except Exception as e:
        logger.error(f"Erreur entraînement background: {str(e)}")
        # Rollback en cas d'erreur
        db.rollback()
        try:
            cursor.execute("""
                UPDATE ml_experiments
                SET status = 'failed', error_message = %s
                WHERE id = %s
            """, (str(e), experiment_id))
            db.commit()
        except Exception as update_error:
            logger.error(f"Erreur mise à jour statut failed: {str(update_error)}")
    finally:
        cursor.close()
        db.close()

@app.get("/ml/experiments/{experiment_id}")
async def get_experiment(experiment_id: int):
    """Get experiment details"""
    db = get_db_connection()
    cursor = db.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                id, name, description, algorithm, hyperparameters,
                target_column, feature_columns, train_ratio, random_seed,
                metrics, confusion_matrix, roc_data, residuals, predictions,
                training_time, model_path, status, error_message,
                created_at, completed_at, project_id, dataset_id,
                transformations_path
            FROM ml_experiments
            WHERE id = %s
        """, (experiment_id,))
        
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        # Parser les champs JSONB
        feature_columns = result[6]
        if isinstance(feature_columns, str):
            feature_columns = json.loads(feature_columns)
        
        hyperparameters = result[4]
        if hyperparameters and isinstance(hyperparameters, str):
            hyperparameters = json.loads(hyperparameters)
        
        metrics = result[9]
        if metrics and isinstance(metrics, str):
            metrics = json.loads(metrics)
        
        confusion_matrix = result[10]
        if confusion_matrix and isinstance(confusion_matrix, str):
            confusion_matrix = json.loads(confusion_matrix)
        
        roc_data = result[11]
        if roc_data and isinstance(roc_data, str):
            roc_data = json.loads(roc_data)
        
        residuals = result[12]
        if residuals and isinstance(residuals, str):
            residuals = json.loads(residuals)
        
        predictions = result[13]
        if predictions and isinstance(predictions, str):
            predictions = json.loads(predictions)
        
        logger.info(f"Experiment {experiment_id} - feature_columns type: {type(feature_columns)}, value: {feature_columns}")
        
        # ✅ FIX : Gérer les dates qui peuvent être None ou déjà des timestamps
        created_at = result[18]
        completed_at = result[19]
        
        # Convertir en ISO format seulement si ce n'est pas None
        if created_at:
            if hasattr(created_at, 'isoformat'):
                created_at = created_at.isoformat()
            else:
                # Si c'est déjà une string ou un timestamp, le garder tel quel
                created_at = str(created_at)
        
        if completed_at:
            if hasattr(completed_at, 'isoformat'):
                completed_at = completed_at.isoformat()
            else:
                completed_at = str(completed_at)
        
        return {
            'id': result[0],
            'name': result[1],
            'description': result[2],
            'algorithm': result[3],
            'hyperparameters': hyperparameters,
            'target_column': result[5],
            'feature_columns': feature_columns,
            'train_ratio': result[7],
            'random_seed': result[8],
            'metrics': metrics,
            'confusion_matrix': confusion_matrix,
            'roc_data': roc_data,
            'residuals': residuals,
            'predictions': predictions,
            'training_time': result[14],
            'model_path': result[15],
            'status': result[16],
            'error_message': result[17],
            'created_at': created_at,
            'completed_at': completed_at,
            'project_id': result[20],
            'dataset_id': result[21],
            'transformations_path': result[22] if len(result) > 22 else None  # ✅ NOUVEAU
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting experiment: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


@app.get("/ml/experiments/list/{dataset_id}")
async def list_experiments(dataset_id: int):
    """Lister toutes les expériences d'un dataset"""
    db = get_db_connection()
    cursor = db.cursor()
    
    try:
        cursor.execute("""
            SELECT id, name, algorithm, status, metrics, training_time, created_at
            FROM ml_experiments
            WHERE dataset_id = %s
            ORDER BY created_at DESC
        """, (dataset_id,))
        
        results = cursor.fetchall()
        
        experiments = []
        for row in results:
            experiments.append({
                'id': row[0],
                'name': row[1],
                'algorithm': row[2],
                'status': row[3],
                'metrics': row[4] if isinstance(row[4], dict) else json.loads(row[4]) if row[4] else None,
                'training_time': row[5],
                'created_at': row[6]
            })
        
        return {'experiments': experiments}
        
    except Exception as e:
        logger.error(f"Erreur liste expériences: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


@app.get("/ml/algorithms")
async def get_algorithms():
    """List available algorithms"""
    return {
        'algorithms': [
            {
                'id': 'knn',
                'name': 'K-Nearest Neighbors',
                'type': 'classification',
                'description': 'Instance-based learning algorithm using k nearest neighbors'
            },
            {
                'id': 'decision_tree',
                'name': 'Decision Tree (CART)',
                'type': 'classification',
                'description': 'Classification and Regression Trees using Gini or Entropy'
            },
            {
                'id': 'c45',
                'name': 'C4.5 Decision Tree',
                'type': 'classification',
                'description': 'Decision tree using Information Gain (Entropy-based splitting)'
            },
            {
                'id': 'chaid',
                'name': 'CHAID Decision Tree',
                'type': 'classification',
                'description': 'Chi-squared Automatic Interaction Detection (statistical tree)'
            },
            {
                'id': 'naive_bayes',
                'name': 'Naive Bayes',
                'type': 'classification',
                'description': 'Probabilistic classifier based on Bayes theorem'
            },
            {
                'id': 'neural_network',
                'name': 'Neural Network (MLP)',
                'type': 'classification',
                'description': 'Multi-layer Perceptron with backpropagation'
            },
            {
                'id': 'linear_regression',
                'name': 'Linear Regression',
                'type': 'regression',
                'description': 'Simple and multiple linear regression with polynomial support'
            }
        ]
    }

@app.get("/ml/algorithms/{algorithm_name}/params")
async def get_algorithm_params(algorithm_name: str):
    """Get algorithm parameters"""
    try:
        if algorithm_name == 'knn':
            from app.ml.algorithms.knn import KNNAlgorithm
            return {'algorithm': algorithm_name, 'parameters': KNNAlgorithm.get_param_ranges()}
        elif algorithm_name == 'decision_tree':
            from app.ml.algorithms.decision_tree import DecisionTreeAlgorithm
            return {'algorithm': algorithm_name, 'parameters': DecisionTreeAlgorithm.get_param_ranges()}
        elif algorithm_name == 'c45':
            from app.ml.algorithms.c45_tree import C45Algorithm
            return {'algorithm': algorithm_name, 'parameters': C45Algorithm.get_param_ranges()}
        elif algorithm_name == 'chaid':
            from app.ml.algorithms.chaid_tree import CHAIDAlgorithm
            return {'algorithm': algorithm_name, 'parameters': CHAIDAlgorithm.get_param_ranges()}
        elif algorithm_name == 'naive_bayes':
            from app.ml.algorithms.naive_bayes import NaiveBayesAlgorithm
            return {'algorithm': algorithm_name, 'parameters': NaiveBayesAlgorithm.get_param_ranges()}
        elif algorithm_name == 'neural_network':
            from app.ml.algorithms.neural_network import NeuralNetworkAlgorithm
            return {'algorithm': algorithm_name, 'parameters': NeuralNetworkAlgorithm.get_param_ranges()}
        elif algorithm_name == 'linear_regression':
            from app.ml.algorithms.linear_regression import LinearRegressionAlgorithm
            return {'algorithm': algorithm_name, 'parameters': LinearRegressionAlgorithm.get_param_ranges()}
        else:
            raise HTTPException(status_code=404, detail="Algorithm not found")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting algorithm params: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))    


@app.get("/ml/experiments/{experiment_id}/tree-visualization")
async def visualize_tree(experiment_id: int):
    """Generate decision tree visualization"""
    db = get_db_connection()
    cursor = db.cursor()
    
    try:
        # Récupérer l'expérience
        cursor.execute("""
            SELECT algorithm, model_path, hyperparameters, project_id
            FROM ml_experiments
            WHERE id = %s AND status = 'completed'
        """, (experiment_id,))
        
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(
                status_code=404, 
                detail="Experiment not found or not completed"
            )
        
        algorithm = result[0]
        model_path = result[1]
        project_id = result[3]
        
        # Vérifier que c'est un arbre de décision
        if algorithm not in ['decision_tree', 'c45', 'chaid']:
            raise HTTPException(
                status_code=400,
                detail="Tree visualization only available for decision tree algorithms (CART, C4.5, CHAID)"
            )
        
        if not model_path or not os.path.exists(model_path):
            raise HTTPException(
                status_code=404,
                detail=f"Model file not found at path: {model_path}"
            )
        
        # Charger le modèle
        import joblib
        model = joblib.load(model_path)
        
        logger.info(f"Loaded model for visualization: {algorithm}")
        
        # Générer la visualisation selon le type
        if algorithm == 'chaid':
            # Pour CHAID, essayer d'utiliser sa méthode de visualisation
            try:
                if hasattr(model, 'tree'):
                    # CHAID wrapper
                    tree_repr = repr(model.tree)
                    return {
                        'type': 'text',
                        'content': tree_repr,
                        'algorithm': algorithm
                    }
                else:
                    # Fallback pour sklearn
                    return {
                        'type': 'text',
                        'content': 'CHAID tree visualization not fully supported with this model type',
                        'algorithm': algorithm
                    }
            except Exception as e:
                logger.error(f"CHAID visualization error: {str(e)}")
                return {
                    'type': 'text',
                    'content': f'CHAID tree structure (text representation not available): {str(e)}',
                    'algorithm': algorithm
                }
        else:
            # Pour CART et C4.5 (sklearn DecisionTreeClassifier)
            try:
                from sklearn.tree import export_graphviz
                import graphviz
                
                # Vérifier que le modèle a les attributs nécessaires
                if not hasattr(model, 'tree_'):
                    raise HTTPException(
                        status_code=500,
                        detail="Model does not have tree structure"
                    )
                
                # Générer le graphviz
                dot_data = export_graphviz(
                    model,
                    out_file=None,
                    filled=True,
                    rounded=True,
                    special_characters=True,
                    class_names=[str(cls) for cls in model.classes_],
                    feature_names=[f'Feature_{i}' for i in range(model.n_features_in_)],
                    impurity=True,
                    proportion=True
                )
                
                # Créer le graphe
                graph = graphviz.Source(dot_data)
                
                # Rendre en PNG et encoder en base64
                png_data = graph.pipe(format='png')
                img_base64 = base64.b64encode(png_data).decode('utf-8')
                
                logger.info(f"Tree visualization generated successfully for {algorithm}")
                
                return {
                    'type': 'image',
                    'content': img_base64,
                    'algorithm': algorithm
                }
                
            except ImportError as e:
                logger.error(f"Graphviz not installed: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail="Graphviz not installed. Please install graphviz system package."
                )
            except Exception as e:
                logger.error(f"Tree visualization error: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to generate tree visualization: {str(e)}"
                )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in tree visualization: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()



from fastapi.responses import FileResponse

@app.get("/ml/experiments/{experiment_id}/download-model")
async def download_model(experiment_id: int):
    """Download trained model file"""
    db = get_db_connection()
    cursor = db.cursor()
    
    try:
        cursor.execute("""
            SELECT model_path, name, algorithm
            FROM ml_experiments
            WHERE id = %s AND status = 'completed'
        """, (experiment_id,))
        
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Experiment not found or not completed")
        
        model_path = result[0]
        exp_name = result[1]
        algorithm = result[2]
        
        if not model_path or not os.path.exists(model_path):
            raise HTTPException(status_code=404, detail="Model file not found")
        
        # Nom du fichier pour le téléchargement
        filename = f"{exp_name}_{algorithm}_model.pkl".replace(" ", "_")
        
        return FileResponse(
            path=model_path,
            media_type='application/octet-stream',
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading model: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()


@app.post("/ml/experiments/{experiment_id}/predict")
async def predict_with_model(experiment_id: int, request: dict):
    """Make predictions with automatic preprocessing"""
    db = get_db_connection()
    cursor = db.cursor()
    
    try:
        # Récupérer le modèle et sa config
        cursor.execute("""
            SELECT model_path, feature_columns, algorithm, transformations_path
            FROM ml_experiments
            WHERE id = %s AND status = 'completed'
        """, (experiment_id,))
        
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        model_path = result[0]
        feature_columns = result[1] if isinstance(result[1], list) else json.loads(result[1])
        algorithm = result[2]
        transformations_path = result[3]
        
        if not model_path or not os.path.exists(model_path):
            raise HTTPException(status_code=404, detail="Model file not found")
        
        # Charger le modèle
        model = joblib.load(model_path)
        logger.info(f"✅ Loaded model from {model_path}")
        
        # Extraire les données d'entrée
        input_data = request.get('data', [])
        
        if not input_data:
            raise HTTPException(status_code=400, detail="No input data provided")
        
        # Convertir en DataFrame
        df = pd.DataFrame(input_data)
        logger.info(f"📊 Received {len(df)} samples with columns: {df.columns.tolist()}")
        
        # ✅ NOUVEAU : Appliquer les transformations si disponibles
        if transformations_path and os.path.exists(transformations_path):
            logger.info("🔄 Applying saved transformations...")
            try:
                preprocessor = DataPreprocessor(transformations_path)
                df_transformed = preprocessor.transform(df)
                logger.info("✅ Transformations applied successfully")
            except Exception as e:
                logger.error(f"❌ Error applying transformations: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Transformation error: {str(e)}")
        else:
            logger.warning("⚠️  No transformations found. Using raw data.")
            # Vérifier les colonnes
            missing_cols = set(feature_columns) - set(df.columns)
            if missing_cols:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required columns: {missing_cols}"
                )
            df_transformed = df[feature_columns]
        
        # Convertir en numpy array
        X = df_transformed.values
        
        # Gérer les valeurs manquantes
        if np.isnan(X).any():
            logger.warning("⚠️  Input contains NaN values. Filling with 0...")
            X = np.nan_to_num(X, nan=0.0)
        
        # Prédictions
        predictions = model.predict(X)
        logger.info(f"✅ Predictions: {predictions}")
        
        # Probabilités (si disponible)
        probabilities = None
        if hasattr(model, 'predict_proba'):
            probabilities = model.predict_proba(X).tolist()
        
        return {
            'predictions': predictions.tolist(),
            'probabilities': probabilities,
            'algorithm': algorithm,
            'n_samples': len(predictions),
            'transformations_applied': transformations_path is not None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Prediction error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        db.close()