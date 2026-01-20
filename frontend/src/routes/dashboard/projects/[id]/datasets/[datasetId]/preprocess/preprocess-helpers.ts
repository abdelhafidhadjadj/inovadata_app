/**
 * Helpers pour la page de preprocessing
 */

export interface ColumnAnalysis {
  name: string;
  data_type: string;
  total_count: number;
  standard_missing_count: number;
  custom_missing_count: number;
  total_missing_count: number;
  missing_percentage: number;
  unique_count: number;
  suspicious_values?: string[];
  value_frequencies?: Record<string, number>;
  statistics?: {
    mean: number;
    std: number;
    min: number;
    max: number;
    median: number;
    q25: number;
    q75: number;
  };
  outliers?: {
    iqr?: {
      outliers_count: number;
      lower_bound: number;
      upper_bound: number;
      q1: number;
      q3: number;
      iqr: number;
      multiplier: number;
    };
    zscore?: {
      outliers_count: number;
      mean: number;
      std: number;
      threshold: number;
    };
    range?: {
      outliers_count: number;
      min_value?: number;
      max_value?: number;
    };
  };
  configured_range?: {
    min?: number;
    max?: number;
  };
}

export interface CustomRanges {
  [columnName: string]: {
    min?: number;
    max?: number;
  };
}

export interface CustomMissingValues {
  [columnName: string]: string;
}

/**
 * Initialise customRanges pour toutes les colonnes numériques
 */
export function initializeCustomRanges(analysis: ColumnAnalysis[]): CustomRanges {
  const ranges: CustomRanges = {};
  
  analysis.forEach(col => {
    if (col.data_type === 'numerical') {
      ranges[col.name] = {};
      
      // Si une configuration existe déjà, l'utiliser
      if (col.configured_range) {
        ranges[col.name] = {
          min: col.configured_range.min,
          max: col.configured_range.max
        };
      }
    }
  });
  
  return ranges;
}

/**
 * Initialise customMissingValues avec les valeurs suspectes détectées
 */
export function initializeCustomMissingValues(analysis: ColumnAnalysis[]): CustomMissingValues {
  const missingValues: CustomMissingValues = {};
  
  analysis.forEach(col => {
    if (col.suspicious_values && col.suspicious_values.length > 0) {
      missingValues[col.name] = col.suspicious_values.join(', ');
    }
  });
  
  return missingValues;
}

/**
 * Calcule le nombre total d'outliers pour une colonne
 */
export function getTotalOutliers(column: ColumnAnalysis): number {
  if (!column.outliers) return 0;
  
  let total = 0;
  if (column.outliers.iqr) total += column.outliers.iqr.outliers_count || 0;
  if (column.outliers.zscore) total += column.outliers.zscore.outliers_count || 0;
  if (column.outliers.range) total += column.outliers.range.outliers_count || 0;
  
  return total;
}

/**
 * Construit l'URL avec les paramètres de configuration
 */
export function buildConfigUrl(
  baseUrl: string,
  columnName: string,
  ranges: CustomRanges,
  missingValues: CustomMissingValues
): string {
  const params = new URLSearchParams(window.location.search);
  
  const range = ranges[columnName];
  
  // Add range params
  if (range?.min !== undefined && range?.min !== null && !isNaN(range.min)) {
    params.set(`${columnName}_min`, range.min.toString());
  } else {
    params.delete(`${columnName}_min`);
  }
  
  if (range?.max !== undefined && range?.max !== null && !isNaN(range.max)) {
    params.set(`${columnName}_max`, range.max.toString());
  } else {
    params.delete(`${columnName}_max`);
  }
  
  // Add custom missing values
  if (missingValues[columnName] && missingValues[columnName].trim()) {
    params.set(`${columnName}_missing`, missingValues[columnName]);
  } else {
    params.delete(`${columnName}_missing`);
  }
  
  return `${baseUrl}?${params.toString()}`;
}

/**
 * Assure qu'un objet range existe pour une colonne
 */
export function ensureRangeExists(
  columnName: string,
  ranges: CustomRanges
): CustomRanges {
  if (!ranges[columnName]) {
    ranges[columnName] = {};
  }
  return ranges;
}