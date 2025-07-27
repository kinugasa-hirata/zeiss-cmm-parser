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
        
        # Column translation mapping
        self.column_translation = {
            'element_name': '要素名',
            'measurement_type': '測定種別',
            'coordinate_name': '座標名', 
            'coordinate_type': '座標種別',
            'measured_value': '実測値',
            'expected_value': '基準値',
            'calculated_deviation': '偏差',
            'upper_tolerance': '上許容差',
            'lower_tolerance': '下許容差',
            'within_tolerance': '許容範囲内',
            'status': 'ステータス',
            'data_type': 'データ種別',
            'has_colored_values': 'カラー値有無',
            'point_count': '点数',
            'side': '側面',
            'std_dev': '標準偏差',
            'min_value': '最小値',
            'max_value': '最大値',
            'form_error': '形状誤差',
            'histogram': 'ヒストグラム',
            'tolerance_range': '許容範囲',
            'tolerance_utilization': '許容差使用率'
        }
        
    def parse_lines_to_dataframe(self, lines: List[str], use_japanese_columns: bool = True) -> pd.DataFrame:
        """
        Parse CMM measurement lines into a structured DataFrame using improved parsing logic.
        
        Args:
            lines: List of strings from CMM measurement data
            use_japanese_columns: Whether to use Japanese column names (default: True)
        
        Returns:
            pandas.DataFrame: Structured measurement data with Japanese column names
        
        Example:
            >>> lines = text.split('\\n')  # Your CMM report text
            >>> df = parser.parse_lines_to_dataframe(lines)
            >>> print(f"Parsed {len(df)} measurements")
        """
        
        print("🔧 Parsing CMM measurement data...")
        print("=" * 60)
        
        # Step 1: Split into datasets using horizontal separators
        datasets = []
        current_dataset = []
        
        separator_pattern = r'^[=_-]{10,}$'  # Long horizontal lines
        header_pattern = r'(CARL ZEISS|CALYPSO|測定ﾌﾟﾗﾝ|ACCURA|名前|説明|実測値|基準値|上許容差|下許容誤差|ﾋｽﾄｸﾞﾗﾑ)'
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Skip page headers
            if re.search(header_pattern, line):
                continue
                
            # If we hit a separator, save current dataset and start new one
            if re.search(separator_pattern, line):
                if current_dataset:
                    datasets.append(current_dataset)
                    current_dataset = []
            else:
                current_dataset.append(line)
        
        # Don't forget the last dataset
        if current_dataset:
            datasets.append(current_dataset)
        
        print(f"📊 Found {len(datasets)} datasets")
        
        # Step 2: Process each dataset with improved patterns
        measurement_records = []
        
        for dataset_idx, dataset in enumerate(datasets):
            if not dataset:  # Skip empty datasets
                continue
                
            # Find element identifier (first line of dataset, more flexible)
            blue_tag = None
            element_info = {}
            stats_info = {}
            
            for line_idx, line in enumerate(dataset):
                # Improved element pattern for actual data
                element_pattern = r'^([^\s]+)\s+(円\(最小二乗法\)|平面\(最小二乗法\)|直線\(最小二乗法\)|基本座標系|3次元直線|点|2D距離)\s*.*?点数\s*\((\d+)\)\s*(内側|外側)?'
                element_match = re.search(element_pattern, line)
                
                if element_match:
                    blue_tag = element_match.group(1)
                    element_info = {
                        'element_name': blue_tag,
                        'measurement_type': element_match.group(2),
                        'point_count': int(element_match.group(3)) if element_match.group(3) else 0,
                        'side': element_match.group(4) if element_match.group(4) else 'N/A'
                    }
                    continue
                
                # Flexible element pattern for simple cases
                if not blue_tag and line_idx == 0:
                    simple_element_pattern = r'^([^\s]+)\s+(円\(最小二乗法\)|平面\(最小二乗法\)|直線\(最小二乗法\)|基本座標系|3次元直線|点|2D距離)'
                    simple_match = re.search(simple_element_pattern, line)
                    if simple_match:
                        blue_tag = simple_match.group(1)
                        element_info = {
                            'element_name': blue_tag,
                            'measurement_type': simple_match.group(2),
                            'point_count': 0,
                            'side': 'N/A'
                        }
                        continue
                
                # Stats pattern for statistical information
                stats_pattern = r'S=\s*([\d.]+)\s+Min=\((\d+)\)\s*([-\d.]+)\s+Max=\((\d+)\)\s*([-\d.]+)\s+形状=\s*([\d.]+)'
                stats_match = re.search(stats_pattern, line)
                if stats_match:
                    stats_info = {
                        'std_dev': float(stats_match.group(1)),
                        'min_point': int(stats_match.group(2)),
                        'min_value': float(stats_match.group(3)),
                        'max_point': int(stats_match.group(4)),
                        'max_value': float(stats_match.group(5)),
                        'form_error': float(stats_match.group(6))
                    }
                    continue
                
                # Coordinate patterns for actual data
                if blue_tag:  # Only process coordinates if we have an element
                    
                    # Named coordinates with full tolerance data (COLORED VALUES)
                    named_coord_pattern = r'^([XYZ]-値_[^\s]*|Y-値_[^\s]*|X-値_[^\s]*|\d+)\s+([XYZ]|D)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s*(.*)?'
                    named_match = re.search(named_coord_pattern, line)
                    
                    if named_match:
                        record = element_info.copy()
                        record.update(stats_info)
                        record.update({
                            'coordinate_name': named_match.group(1),
                            'coordinate_type': named_match.group(2),
                            'measured_value': float(named_match.group(3)),
                            'expected_value': float(named_match.group(4)),
                            'upper_tolerance': float(named_match.group(5)),
                            'lower_tolerance': float(named_match.group(6)),
                            'calculated_deviation': float(named_match.group(7)),
                            'histogram': named_match.group(8).strip() if named_match.group(8) else '',
                            'data_type': 'named_coordinate_with_tolerance',
                            'has_colored_values': True  # These would be colored in original
                        })
                        measurement_records.append(record)
                        continue
        
        print(f"\n📊 EXTRACTION SUMMARY:")
        print(f"✅ Total datasets processed: {len(datasets)}")
        print(f"✅ Total measurement records: {len(measurement_records)}")
        
        if measurement_records:
            df = pd.DataFrame(measurement_records)
            
            # Calculate additional fields
            df['within_tolerance'] = df.apply(lambda row: 
                row['lower_tolerance'] <= row['calculated_deviation'] <= row['upper_tolerance'] 
                if pd.notna(row['lower_tolerance']) and pd.notna(row['upper_tolerance']) and pd.notna(row['calculated_deviation'])
                else None, axis=1
            )
            
            df['status'] = df['within_tolerance'].map({True: 'PASS', False: 'FAIL', None: 'N/A'})
            
            # Add tolerance utilization calculation
            df['tolerance_range'] = df['upper_tolerance'] - df['lower_tolerance']
            df['tolerance_utilization'] = np.where(
                df['tolerance_range'] != 0,
                (df['calculated_deviation'].abs() / (df['tolerance_range'] / 2) * 100).round(2),
                0
            )
            
            # Convert to Japanese column names if requested
            if use_japanese_columns:
                df = df.rename(columns=self.column_translation)
                
                japanese_column_order = [
                    '要素名', '測定種別', '座標名', '座標種別',
                    '実測値', '基準値', '偏差',
                    '上許容差', '下許容差', '許容範囲', '許容範囲内', '許容差使用率', 'ステータス',
                    'データ種別', 'カラー値有無', '点数', '側面',
                    '標準偏差', '最小値', '最大値', '形状誤差', 'ヒストグラム'
                ]
            else:
                japanese_column_order = [
                    'element_name', 'measurement_type', 'coordinate_name', 'coordinate_type',
                    'measured_value', 'expected_value', 'calculated_deviation',
                    'upper_tolerance', 'lower_tolerance', 'tolerance_range', 'within_tolerance', 'tolerance_utilization', 'status',
                    'data_type', 'has_colored_values', 'point_count', 'side',
                    'std_dev', 'min_value', 'max_value', 'form_error', 'histogram'
                ]
            
            available_columns = [col for col in japanese_column_order if col in df.columns]
            df = df[available_columns]
            
            print(f"✅ DataFrame created with {len(df)} records and Japanese column names!")
            return df
        else:
            print("❌ No measurement records found")
            return pd.DataFrame()
    
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
        
        # Handle both Japanese and English column names
        element_col = '要素名' if '要素名' in df.columns else 'element_name'
        measured_col = '実測値' if '実測値' in df.columns else 'measured_value'
        deviation_col = '偏差' if '偏差' in df.columns else 'calculated_deviation'
        tolerance_col = '許容範囲内' if '許容範囲内' in df.columns else 'within_tolerance'
        util_col = '許容差使用率' if '許容差使用率' in df.columns else 'tolerance_utilization'
        type_col = '測定種別' if '測定種別' in df.columns else 'measurement_type'
        point_col = '点数' if '点数' in df.columns else 'point_count'
        side_col = '側面' if '側面' in df.columns else 'side'
        
        summary = df.groupby(element_col).agg({
            type_col: 'first',
            point_col: 'first',
            side_col: 'first',
            measured_col: ['count', 'mean', 'std'],
            deviation_col: ['mean', 'std', 'min', 'max'],
            tolerance_col: 'sum',
            util_col: 'mean'
        }).round(4)
        
        summary.columns = ['_'.join(col).strip() for col in summary.columns.values]
        summary = summary.rename(columns={
            f'{measured_col}_count': 'coordinate_count',
            f'{measured_col}_mean': 'avg_measured_value',
            f'{measured_col}_std': 'std_measured_value',
            f'{deviation_col}_mean': 'avg_deviation',
            f'{deviation_col}_std': 'std_deviation',
            f'{deviation_col}_min': 'min_deviation',
            f'{deviation_col}_max': 'max_deviation',
            f'{tolerance_col}_sum': 'pass_count',
            f'{util_col}_mean': 'avg_tolerance_util'
        })
        
        summary['pass_rate'] = (summary['pass_count'] / summary['coordinate_count'] * 100).round(1)
        return summary.reset_index()


def parse_cmm_data(lines: List[str], use_japanese_columns: bool = True) -> pd.DataFrame:
    """
    Quick function to parse CMM measurement lines to DataFrame.
    
    Args:
        lines: List of strings from CMM measurement data
        use_japanese_columns: Whether to use Japanese column names
        
    Returns:
        pandas.DataFrame: Structured measurement data
        
    Example:
        >>> import cmm_measurement_parser as cmp
        >>> lines = text.split('\\n')
        >>> df = cmp.parse_cmm_data(lines)
    """
    parser = CMMParser()
    return parser.parse_lines_to_dataframe(lines, use_japanese_columns)


def process_cmm_data(lines: List[str], use_japanese_columns: bool = True) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Complete CMM data processing pipeline.
    
    Args:
        lines: List of strings from CMM measurement data
        use_japanese_columns: Whether to use Japanese column names
        
    Returns:
        Tuple of (detailed_df, summary_df)
        
    Example:
        >>> df, summary = process_cmm_data(lines)
        >>> print(f"Processed {len(df)} measurements from {len(summary)} elements")
    """
    parser = CMMParser()
    df = parser.parse_lines_to_dataframe(lines, use_japanese_columns)
    
    if len(df) == 0:
        print("❌ No data parsed successfully")
        return pd.DataFrame(), pd.DataFrame()
    
    summary_df = parser.create_summary_by_element(df)
    
    # Show statistics
    status_col = 'ステータス' if use_japanese_columns else 'status'
    element_col = '要素名' if use_japanese_columns else 'element_name'
    
    pass_count = len(df[df[status_col] == 'PASS'])
    total_count = len(df)
    pass_rate = (pass_count / total_count * 100) if total_count > 0 else 0
    
    print(f"📊 Processing Complete:")
    print(f"   📏 {total_count} measurements")
    print(f"   🔧 {df[element_col].nunique()} elements")
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