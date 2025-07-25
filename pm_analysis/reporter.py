#!/usr/bin/env python3
"""
Functions for reporting and analyzing production method profitability.
"""

import pandas as pd
from typing import Dict, Any

def get_summary_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """Get summary statistics of profitability analysis."""
    if df.empty:
        return {}
    
    # Filter out None values for statistics
    finite_profit = df[df['profit_per_employee'].notna()].copy()
    
    stats = {
        'total_pms': len(df),
        'profitable_pms': len(df[df['total_profit'] > 0]),
        'unprofitable_pms': len(df[df['total_profit'] < 0]),
        'break_even_pms': len(df[df['total_profit'] == 0]),
        'avg_total_profit': df['total_profit'].mean(),
        'median_total_profit': df['total_profit'].median(),
        'max_total_profit': df['total_profit'].max(),
        'min_total_profit': df['total_profit'].min(),
        'avg_profit_per_employee': finite_profit['profit_per_employee'].mean() if not finite_profit.empty else 0,
        'median_profit_per_employee': finite_profit['profit_per_employee'].median() if not finite_profit.empty else 0,
        'max_profit_per_employee': finite_profit['profit_per_employee'].max() if not finite_profit.empty else 0,
        'min_profit_per_employee': finite_profit['profit_per_employee'].min() if not finite_profit.empty else 0,
        'total_missing_input_prices': sum(len(pm) for pm in df['missing_input_prices']),
        'total_missing_output_prices': sum(len(pm) for pm in df['missing_output_prices']),
    }
    
    return stats

def save_analysis(df: pd.DataFrame, output_path: str = "pm_profitability_analysis.csv") -> None:
    """Save the profitability analysis to CSV."""
    if not df.empty:
        # Create a simplified version for CSV export
        export_df = df[['production_method_name', 'parent_building', 'filename', 
                       'total_employment', 'input_cost', 'output_revenue', 
                       'total_profit', 'profit_per_employee']].copy()
        
        export_df.to_csv(output_path, index=False)
        print(f"Analysis saved to {output_path}")
    else:
        print("No data to save")

def print_top_profitable_pms(df: pd.DataFrame, top_n: int = 10) -> None:
    """Print the most profitable production methods."""
    if df.empty:
        print("No data to analyze")
        return
    
    print(f"\n=== TOP {top_n} MOST PROFITABLE PRODUCTION METHODS ===")
    
    # Sort by total profit
    top_by_total = df.nlargest(top_n, 'total_profit')
    print(f"\nBy Total Profit:")
    for _, pm in top_by_total.iterrows():
        print(f"{pm['production_method_name']:40} | Profit: {pm['total_profit']:8.1f} | Per Employee: {pm['profit_per_employee']:6.1f} | Employment: {pm['total_employment']:4}")
    
    # Sort by profit per employee (excluding None values)
    finite_df = df[df['profit_per_employee'].notna()].copy()
    
    if not finite_df.empty:
        top_by_per_employee = finite_df.nlargest(top_n, 'profit_per_employee', keep='first')
        print(f"\nBy Profit Per Employee:")
        for _, pm in top_by_per_employee.iterrows():
            print(f"{pm['production_method_name']:40} | Profit: {pm['total_profit']:8.1f} | Per Employee: {pm['profit_per_employee']:6.1f} | Employment: {pm['total_employment']:4}")

def print_employment_analysis(df: pd.DataFrame) -> None:
    """Print analysis of employment data quality."""
    if df.empty:
        print("No data to analyze")
        return
    
    print(f"\n=== EMPLOYMENT DATA ANALYSIS ===")
    
    # Count PMs with different employment statuses
    zero_employment = df[df['total_employment'] == 0]
    negative_employment = df[df['total_employment'] < 0]
    positive_employment = df[df['total_employment'] > 0]
    
    print(f"PMs with zero employment: {len(zero_employment)} ({len(zero_employment)/len(df)*100:.1f}%)")
    print(f"PMs with negative employment: {len(negative_employment)} ({len(negative_employment)/len(df)*100:.1f}%)")
    print(f"PMs with positive employment: {len(positive_employment)} ({len(positive_employment)/len(df)*100:.1f}%)")
    
    # Show examples of PMs with zero employment
    if not zero_employment.empty:
        print(f"\nExamples of PMs with zero employment (likely use default building employment):")
        for _, pm in zero_employment.head(10).iterrows():
            print(f"  {pm['production_method_name']} ({pm['parent_building']})")
    
    # Show examples of PMs with negative employment (automation)
    if not negative_employment.empty:
        print(f"\nExamples of PMs with negative employment (automation):")
        for _, pm in negative_employment.head(10).iterrows():
            print(f"  {pm['production_method_name']} ({pm['parent_building']}) - {pm['total_employment']} employees")
    
    # Employment range for PMs with positive employment
    if not positive_employment.empty:
        print(f"\nEmployment range for PMs with explicit employment:")
        print(f"  Min: {positive_employment['total_employment'].min()}")
        print(f"  Max: {positive_employment['total_employment'].max()}")
        print(f"  Average: {positive_employment['total_employment'].mean():.1f}")
        print(f"  Median: {positive_employment['total_employment'].median():.1f}") 