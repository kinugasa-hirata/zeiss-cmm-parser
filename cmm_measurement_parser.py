"""
CMM Measurement Parser
=====================

A professional Python package for parsing CMM (Coordinate Measuring Machine) measurement data
from Japanese measurement reports (Carl Zeiss CALYPSO format).

Features:
- Parse Japanese CMM measurement reports to structured DataFrames
- Automatic tolerance analysis with PASS/FAIL determination  
- Export to Excel with proper Japanese character encoding
- Summary statistics by measurement element
- Professional quality control reporting

Author: shuhei
License: MIT
"""

import pandas as pd
import re
import numpy as np
from typing import List, Dict, Tuple, Optional
import datetime

class CMMParser:
    """
    Professional CMM measurement data parser for coordinate measuring machines.
    
    Supports Carl Zeiss CALYPSO format and Japanese measurement reports.
    
    Example:
        >>> parser = CMMParser()
        >>> df = parser.parse_lines_to_dataframe(lines)
        >>> summary = parser.create_summary_by_element(df)
    """
    
    def __init__(self):
        """Initialize the CMM Parser"""
        self.version = "1.0.0"
        
    def parse_lines_to_dataframe(self, lines: List[str]) -> pd.DataFrame:
        """
        Parse CMM measurement lines into a structured DataFrame.
        
        Args:
            lines: List of strings from CMM measurement data
        
        Returns:
            pandas.DataFrame: Structured measurement data with columns:
                - element_name: Name of measurement element (ｄ-1, 円1, etc.)
                - measurement_type: Type of measurement (円(最小二乗法), etc.)
                - coordinate_type: X, Y, Z, or D coordinate
                - measured_value: Actual measured value
                - reference_value: Target/reference value  
                - deviation: Difference from reference
                - upper_tolerance: Upper tolerance limit
                - lower_tolerance: Lower tolerance limit
                - within_tolerance: Boolean pass/fail
                - status: 'PASS' or 'FAIL' string
                - tolerance_utilization: Percentage of tolerance used
        
        Example:
            >>> lines = text.split('\\n')  # Your CMM report text
            >>> df = parser.parse_lines_to_dataframe(lines)
            >>> print(f"Parsed {len(df)} measurements")
        """
        
        print("🔧 Parsing CMM measurement data...")
        
        measurement_records = []
        current_element = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Pattern 1: Detect measurement element
            element_pattern = r'(ｄ-\d+|円\d+|平面\d+|基準円\d+|.*線)\s+(円\(最小二乗法\)|平面\(最小二乗法\)|直線\(最小二乗法\))\s+点数\s+\((\d+)\)\s*(内側|外側)?'
            element_match = re.search(element_pattern, line)
            
            if element_match:
                current_element = {
                    'element_name': element_match.group(1),
                    'measurement_type': element_match.group(2),
                    'point_count': int(element_match.group(3)),
                    'side': element_match.group(4) if element_match.group(4) else 'N/A'
                }
                continue
            
            # Pattern 2: Statistics line
            stats_pattern = r'S=\s*([\d.]+)\s+Min=\([^)]+\)\s*([\-\d.]+)\s+Max=\([^)]+\)\s*([\-\d.]+)\s+形状=\s*([\d.]+)'
            stats_match = re.search(stats_pattern, line)
            
            if stats_match and current_element:
                current_element.update({
                    'std_dev': float(stats_match.group(1)),
                    'min_value': float(stats_match.group(2)),
                    'max_value': float(stats_match.group(3)),
                    'form_error': float(stats_match.group(4))
                })
                continue
            
            # Pattern 3: Coordinate lines with tolerances
            coord_pattern = r'^([XYZ][\-値_\w]*|D)\s+([XYZ]|D)\s+([\-\d.]+)\s+([\-\d.]+)\s+([\-\d.]+)\s+([\-\d.]+)\s+([\-\d.]+)\s*(.*)?'
            coord_match = re.search(coord_pattern, line)
            
            if coord_match and current_element:
                record = current_element.copy()
                record.update({
                    'coordinate_name': coord_match.group(1),
                    'coordinate_type': coord_match.group(2),
                    'measured_value': float(coord_match.group(3)),
                    'reference_value': float(coord_match.group(4)),
                    'upper_tolerance': float(coord_match.group(5)),
                    'lower_tolerance': float(coord_match.group(6)),
                    'deviation': float(coord_match.group(7)),
                    'histogram': coord_match.group(8).strip() if coord_match.group(8) else '',
                    'within_tolerance': float(coord_match.group(6)) <= float(coord_match.group(7)) <= float(coord_match.group(5))
                })
                measurement_records.append(record)
        
        df = pd.DataFrame(measurement_records)
        
        if len(df) > 0:
            # Add calculated columns
            df['tolerance_range'] = df['upper_tolerance'] - df['lower_tolerance']
            df['deviation_abs'] = df['deviation'].abs()
            
            # Avoid division by zero
            mask = df['tolerance_range'] != 0
            df.loc[mask, 'tolerance_utilization'] = (df.loc[mask, 'deviation_abs'] / (df.loc[mask, 'tolerance_range'] / 2) * 100).round(2)
            df.loc[~mask, 'tolerance_utilization'] = 0
            
            df['status'] = df['within_tolerance'].map({True: 'PASS', False: 'FAIL'})
            
            # Reorder columns
            column_order = [
                'element_name', 'measurement_type', 'point_count', 'side',
                'coordinate_name', 'coordinate_type', 
                'measured_value', 'reference_value', 'deviation',
                'upper_tolerance', 'lower_tolerance', 'tolerance_range',
                'within_tolerance', 'tolerance_utilization', 'status',
                'std_dev', 'min_value', 'max_value', 'form_error', 'histogram'
            ]
            available_columns = [col for col in column_order if col in df.columns]
            df = df[available_columns]
        
        print(f"✅ Parsed {len(df)} measurements")
        return df
    
    def create_summary_by_element(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create summary statistics grouped by measurement element.
        
        Args:
            df: Structured CMM DataFrame from parse_lines_to_dataframe()
            
        Returns:
            pd.DataFrame: Summary statistics including pass rates and averages
        """
        if len(df) == 0:
            return pd.DataFrame()
        
        summary = df.groupby('element_name').agg({
            'measurement_type': 'first',
            'point_count': 'first',
            'side': 'first',
            'measured_value': ['count', 'mean', 'std'],
            'deviation': ['mean', 'std', 'min', 'max'],
            'within_tolerance': 'sum',
            'tolerance_utilization': 'mean'
        }).round(4)
        
        summary.columns = ['_'.join(col).strip() for col in summary.columns.values]
        summary = summary.rename(columns={
            'measured_value_count': 'coordinate_count',
            'measured_value_mean': 'avg_measured_value',
            'measured_value_std': 'std_measured_value',
            'deviation_mean': 'avg_deviation',
            'deviation_std': 'std_deviation',
            'deviation_min': 'min_deviation',
            'deviation_max': 'max_deviation',
            'within_tolerance_sum': 'pass_count',
            'tolerance_utilization_mean': 'avg_tolerance_util'
        })
        
        summary['pass_rate'] = (summary['pass_count'] / summary['coordinate_count'] * 100).round(1)
        return summary.reset_index()


def parse_cmm_data(lines: List[str]) -> pd.DataFrame:
    """
    Quick function to parse CMM measurement lines to DataFrame.
    
    Args:
        lines: List of strings from CMM measurement data
        
    Returns:
        pandas.DataFrame: Structured measurement data
        
    Example:
        >>> import cmm_measurement_parser as cmp
        >>> lines = text.split('\\n')
        >>> df = cmp.parse_cmm_data(lines)
    """
    parser = CMMParser()
    return parser.parse_lines_to_dataframe(lines)


def process_cmm_data(lines: List[str]) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Complete CMM data processing pipeline.
    
    Args:
        lines: List of strings from CMM measurement data
        
    Returns:
        Tuple of (detailed_df, summary_df)
        
    Example:
        >>> df, summary = process_cmm_data(lines)
        >>> print(f"Processed {len(df)} measurements from {len(summary)} elements")
    """
    parser = CMMParser()
    df = parser.parse_lines_to_dataframe(lines)
    
    if len(df) == 0:
        print("❌ No data parsed successfully")
        return pd.DataFrame(), pd.DataFrame()
    
    summary_df = parser.create_summary_by_element(df)
    
    # Show statistics
    pass_count = len(df[df['status'] == 'PASS'])
    total_count = len(df)
    pass_rate = (pass_count / total_count * 100) if total_count > 0 else 0
    
    print(f"📊 Processing Complete:")
    print(f"   📏 {total_count} measurements")
    print(f"   🔧 {df['element_name'].nunique()} elements")
    print(f"   ✅ {pass_rate:.1f}% pass rate")
    
    return df, summary_df


def export_to_excel(df: pd.DataFrame, filename: str = 'CMM_Analysis') -> str:
    """
    Export DataFrame to Excel with Japanese character support.
    
    Args:
        df: DataFrame to export
        filename: Base filename (without extension)
        
    Returns:
        str: Generated filename
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_filename = f"{filename}_{timestamp}.xlsx"
    df.to_excel(excel_filename, index=False)
    print(f"✅ Exported: {excel_filename}")
    return excel_filename


# Package metadata
__version__ = "1.0.0"
__author__ = "shuhei"
__license__ = "MIT"
__description__ = "Professional CMM measurement data parser for coordinate measuring machines"