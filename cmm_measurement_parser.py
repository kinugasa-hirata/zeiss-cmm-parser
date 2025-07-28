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
- Filtered XY coordinate extraction with numerical sorting

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
        self.version = "1.2.0"  # Updated version
        
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
            'tolerance_utilization': '許容差使用率',
            'value': '値'
        }
        
    def parse_lines_to_dataframe(self, lines: List[str], use_japanese_columns: bool = True, verbose: bool = False) -> pd.DataFrame:
        """
        Parse CMM measurement lines into a structured DataFrame using improved parsing logic.
        
        Args:
            lines: List of strings from CMM measurement data
            use_japanese_columns: Whether to use Japanese column names (default: True)
            verbose: Whether to print progress messages (default: False)
        
        Returns:
            pandas.DataFrame: Structured measurement data with Japanese column names
        
        Example:
            >>> lines = text.split('\\n')  # Your CMM report text
            >>> df = parser.parse_lines_to_dataframe(lines, verbose=True)
            >>> print(f"Parsed {len(df)} measurements")
        """
        
        if verbose:
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
        
        if verbose:
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
        
        if verbose:
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
            
            if verbose:
                print(f"✅ DataFrame created with {len(df)} records and Japanese column names!")
            return df
        else:
            if verbose:
                print("❌ No measurement records found")
            return pd.DataFrame()

    def parse_xy_coordinates(self, lines: List[str], use_japanese_columns: bool = True, verbose: bool = False) -> pd.DataFrame:
        """
        NEW: Parse only X,Y coordinates from specific element types with numerical sorting.
        
        Extracts only exact "円" + numbers and "ｄ-" + numbers elements,
        creating a clean dataset with two rows per element (X and Y coordinates).
        
        Args:
            lines: List of strings from CMM measurement data
            use_japanese_columns: Whether to use Japanese column names (default: True)
            verbose: Whether to print progress messages (default: False)
        
        Returns:
            pandas.DataFrame: Clean XY coordinate data with numerical sorting
        
        Example:
            >>> parser = CMMParser()
            >>> df = parser.parse_xy_coordinates(lines, verbose=True)
            >>> print(f"Extracted {len(df)} coordinate records")
        """
        
        if verbose:
            print("🔧 Filtered XY Parser - Continuous stream processing...")
            print("=" * 60)

        # Step 1: Clean the lines by removing headers
        clean_lines = []
        header_pattern = r'(CARL ZEISS|CALYPSO|測定ﾌﾟﾗﾝ|ACCURA|名前|説明|実測値|基準値|上許容差|下許容誤差|ﾋｽﾄｸﾞﾗﾑ|ｺﾝﾊﾟｸﾄﾌﾟﾘﾝﾄｱｳﾄ|ｵﾍﾟﾚｰﾀ|日付|ﾊﾟｰﾄNo|Master|2025年|20190821|支持板)'
        separator_pattern = r'^[=_-]{10,}$'
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Skip all header/separator lines
            if re.search(header_pattern, line) or re.search(separator_pattern, line):
                if verbose:
                    print(f"   Skipping header: {line[:50]}...")
                continue
            clean_lines.append(line)

        if verbose:
            print(f"📊 Cleaned document: {len(clean_lines)} useful lines")

        # Step 2: Process all clean lines sequentially
        xy_records = []
        current_element = None
        looking_for_x = False
        looking_for_y = False
        current_x = None

        for line_idx, line in enumerate(clean_lines):
            
            # Look for element patterns
            element_pattern = r'^([^\s]+)\s+(円\(最小二乗法\)|平面\(最小二乗法\)|直線\(最小二乗法\)|基本座標系|3次元直線|点|2D距離)'
            element_match = re.search(element_pattern, line)
            
            if element_match:
                candidate_tag = element_match.group(1)
                
                if verbose:
                    print(f"   Line {line_idx}: Found candidate element '{candidate_tag}'")
                
                # FILTER: Only EXACT matches for "円" + numbers OR "ｄ-" + numbers
                circle_pattern = r'^円\d+$'
                d_pattern = r'^ｄ-\d+$'
                
                if re.search(circle_pattern, candidate_tag) or re.search(d_pattern, candidate_tag):
                    # Save previous record if incomplete
                    if current_element and current_x is not None and looking_for_y:
                        if verbose:
                            print(f"   ⚠️  Previous element {current_element} incomplete (missing Y)")
                    
                    # Start tracking new element
                    current_element = candidate_tag
                    looking_for_x = True
                    looking_for_y = False
                    current_x = None
                    
                    if verbose:
                        tag_type = "円グループ" if "円" in candidate_tag else "ｄ-グループ"
                        print(f"   ✅ ACCEPTED element: {current_element} ({tag_type})")
                else:
                    if verbose:
                        print(f"   ❌ REJECTED element: {candidate_tag} (doesn't match filter)")
                continue

            # Look for X coordinate
            if current_element and looking_for_x:
                x_pattern = r'\bX\s+([-\d.]+)'
                x_match = re.search(x_pattern, line)
                if x_match:
                    current_x = abs(float(x_match.group(1)))
                    looking_for_x = False
                    looking_for_y = True
                    if verbose:
                        print(f"   ✅ Found X for {current_element}: {current_x}")
                    continue

            # Look for Y coordinate
            if current_element and current_x is not None and looking_for_y:
                y_pattern = r'\bY\s+([-\d.]+)'
                y_match = re.search(y_pattern, line)
                if y_match:
                    current_y = abs(float(y_match.group(1)))
                    
                    # Save complete record
                    record = {
                        'element_name': current_element,
                        'x_coordinate': current_x,
                        'y_coordinate': current_y
                    }
                    xy_records.append(record)
                    
                    if verbose:
                        print(f"   ✅ COMPLETE: {current_element} X={current_x} Y={current_y}")
                    
                    # Reset for next element
                    current_element = None
                    looking_for_x = False
                    looking_for_y = False
                    current_x = None
                    continue

        if verbose:
            print(f"\n📊 FILTERED XY EXTRACTION SUMMARY:")
            print(f"✅ Total clean lines processed: {len(clean_lines)}")
            print(f"✅ Total filtered XY records: {len(xy_records)}")

        if xy_records:
            # Separate into groups
            circle_elements = [r for r in xy_records if "円" in r['element_name']]
            d_elements = [r for r in xy_records if "ｄ-" in r['element_name']]
            
            if verbose:
                print(f"\n📊 Groups found:")
                print(f"   円グループ: {len(circle_elements)} elements")
                print(f"   ｄ-グループ: {len(d_elements)} elements")

            # NUMERICAL SORTING FUNCTION
            def extract_number(element_name):
                if "円" in element_name:
                    match = re.search(r'円(\d+)', element_name)
                    return int(match.group(1)) if match else 0
                elif "ｄ-" in element_name:
                    match = re.search(r'ｄ-(\d+)', element_name)
                    return int(match.group(1)) if match else 0
                return 0

            # Create reshaped data with numerical sorting
            reshaped_data = []
            
            # Add 円 group elements (sorted numerically)
            circle_elements_sorted = sorted(circle_elements, key=lambda x: extract_number(x['element_name']))
            for element_record in circle_elements_sorted:
                # Add X row
                reshaped_data.append({
                    'element_name': element_record['element_name'],
                    'coordinate_type': 'X',
                    'value': element_record['x_coordinate']
                })
                # Add Y row
                reshaped_data.append({
                    'element_name': element_record['element_name'],
                    'coordinate_type': 'Y',
                    'value': element_record['y_coordinate']
                })
            
            # Add ｄ- group elements (sorted numerically)
            d_elements_sorted = sorted(d_elements, key=lambda x: extract_number(x['element_name']))
            for element_record in d_elements_sorted:
                # Add X row
                reshaped_data.append({
                    'element_name': element_record['element_name'],
                    'coordinate_type': 'X',
                    'value': element_record['x_coordinate']
                })
                # Add Y row
                reshaped_data.append({
                    'element_name': element_record['element_name'],
                    'coordinate_type': 'Y',
                    'value': element_record['y_coordinate']
                })
            
            df = pd.DataFrame(reshaped_data)
            
            # Convert column names if Japanese requested
            if use_japanese_columns:
                df = df.rename(columns=self.column_translation)

            if verbose:
                print(f"✅ Reshaped DataFrame created!")
                print(f"📐 Shape: {df.shape[0]} rows × {df.shape[1]} columns")
                print(f"📍 Sample data:")
                print(df.head(10))
                
            return df
        else:
            if verbose:
                print("❌ No filtered XY coordinate records found")
            return pd.DataFrame()
    
    def create_summary_by_element(self, df: pd.DataFrame, verbose: bool = False) -> pd.DataFrame:
        """
        Create summary statistics grouped by measurement element.
        
        Args:
            df: Structured CMM DataFrame from parse_lines_to_dataframe()
            verbose: Whether to print progress messages (default: False)
            
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


def parse_cmm_data(lines: List[str], use_japanese_columns: bool = True, verbose: bool = False) -> pd.DataFrame:
    """
    Quick function to parse CMM measurement lines to DataFrame.
    
    Args:
        lines: List of strings from CMM measurement data
        use_japanese_columns: Whether to use Japanese column names
        verbose: Whether to print progress messages (default: False)
        
    Returns:
        pandas.DataFrame: Structured measurement data
        
    Example:
        >>> import cmm_measurement_parser as cmp
        >>> lines = text.split('\\n')
        >>> df = cmp.parse_cmm_data(lines)  # Silent mode
        >>> df = cmp.parse_cmm_data(lines, verbose=True)  # With output
    """
    parser = CMMParser()
    return parser.parse_lines_to_dataframe(lines, use_japanese_columns, verbose)


def parse_xy_coordinates(lines: List[str], use_japanese_columns: bool = True, verbose: bool = False) -> pd.DataFrame:
    """
    NEW: Quick function to parse only X,Y coordinates from specific elements.
    
    Extracts only exact "円" + numbers and "ｄ-" + numbers elements,
    creating a clean dataset with numerical sorting.
    
    Args:
        lines: List of strings from CMM measurement data
        use_japanese_columns: Whether to use Japanese column names (default: True)
        verbose: Whether to print progress messages (default: False)
        
    Returns:
        pandas.DataFrame: Clean XY coordinate data
        
    Example:
        >>> import cmm_measurement_parser as cmp
        >>> df = cmp.parse_xy_coordinates(lines)  # Silent mode
        >>> df = cmp.parse_xy_coordinates(lines, verbose=True)  # With output
    """
    parser = CMMParser()
    return parser.parse_xy_coordinates(lines, use_japanese_columns, verbose)


def process_cmm_data(lines: List[str], use_japanese_columns: bool = True, verbose: bool = False) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Complete CMM data processing pipeline.
    
    Args:
        lines: List of strings from CMM measurement data
        use_japanese_columns: Whether to use Japanese column names
        verbose: Whether to print progress messages (default: False)
        
    Returns:
        Tuple of (detailed_df, summary_df)
        
    Example:
        >>> df, summary = process_cmm_data(lines)  # Silent mode
        >>> df, summary = process_cmm_data(lines, verbose=True)  # With output
        >>> print(f"Processed {len(df)} measurements from {len(summary)} elements")
    """
    parser = CMMParser()
    df = parser.parse_lines_to_dataframe(lines, use_japanese_columns, verbose)
    
    if len(df) == 0:
        if verbose:
            print("❌ No data parsed successfully")
        return pd.DataFrame(), pd.DataFrame()
    
    summary_df = parser.create_summary_by_element(df, verbose)
    
    if verbose:
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


def export_to_excel(df: pd.DataFrame, filename: str = 'CMM_Analysis', verbose: bool = False) -> str:
    """
    Export DataFrame to Excel with Japanese character support.
    
    Args:
        df: DataFrame to export
        filename: Base filename (without extension)
        verbose: Whether to print progress messages (default: False)
        
    Returns:
        str: Generated filename
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_filename = f"{filename}_{timestamp}.xlsx"
    df.to_excel(excel_filename, index=False)
    if verbose:
        print(f"✅ Exported: {excel_filename}")
    return excel_filename


# Package metadata
__version__ = "1.2.0"  # Updated version
__author__ = "shuhei"
__license__ = "MIT"
__description__ = "Professional CMM measurement data parser for coordinate measuring machines with filtered XY extraction"