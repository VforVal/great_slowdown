#!/usr/bin/env python3
"""
Script to analyze Victoria 3 production methods profitability.
Combines PM data with goods prices to calculate total profitability and profitability per employee.
"""

import pandas as pd
import ast
import re
from pathlib import Path
from typing import Dict, Any

class PMProfitabilityAnalyzer:
    def __init__(self, pm_csv_path: str = "production_methods.csv", goods_file_path: str = "common/goods/00_goods.txt"):
        self.pm_csv_path = pm_csv_path
        self.goods_file_path = goods_file_path
        self.goods_prices = {}
        self.pm_data = None
        
    def load_goods_prices(self) -> Dict[str, float]:
        """Extract goods prices from the goods file."""
        try:
            with open(self.goods_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Pattern to match goods and their costs
            # Matches: good_name = { ... cost = 20 ... }
            goods_pattern = r'(\w+)\s*=\s*\{[^}]*?cost\s*=\s*(\d+)'
            matches = re.findall(goods_pattern, content, re.DOTALL)
            
            for good_name, cost in matches:
                self.goods_prices[good_name] = float(cost)
            
            print(f"Loaded {len(self.goods_prices)} goods prices")
            return self.goods_prices
            
        except Exception as e:
            print(f"Error loading goods prices: {e}")
            return {}
    
    def load_pm_data(self) -> pd.DataFrame:
        """Load production methods data from CSV."""
        try:
            self.pm_data = pd.read_csv(self.pm_csv_path)
            print(f"Loaded {len(self.pm_data)} production methods")
            return self.pm_data
        except Exception as e:
            print(f"Error loading PM data: {e}")
            return pd.DataFrame()
    
    def calculate_pm_profitability(self) -> pd.DataFrame:
        """Calculate profitability for each production method."""
        if self.pm_data is None or self.pm_data.empty:
            print("No PM data loaded!")
            return pd.DataFrame()
        
        if not self.goods_prices:
            print("No goods prices loaded!")
            return pd.DataFrame()
        
        results = []
        
        for _, row in self.pm_data.iterrows():
            pm_info = {
                'production_method_name': row['production_method_name'],
                'parent_building': row['parent_building'],
                'filename': row['filename'],
                'total_employment': row['total_employment'],
                'input_cost': 0,
                'output_revenue': 0,
                'total_profit': 0,
                'profit_per_employee': 0,
                'input_goods': {},
                'output_goods': {},
                'missing_input_prices': [],
                'missing_output_prices': []
            }
            
            # Parse inputs and calculate input cost
            try:
                inputs = ast.literal_eval(row['inputs']) if row['inputs'] != '{}' else {}
                for good, quantity in inputs.items():
                    if good in self.goods_prices:
                        cost = self.goods_prices[good] * quantity
                        pm_info['input_cost'] += cost
                        pm_info['input_goods'][good] = {
                            'quantity': quantity,
                            'price': self.goods_prices[good],
                            'total_cost': cost
                        }
                    else:
                        pm_info['missing_input_prices'].append(good)
            except:
                pm_info['missing_input_prices'].append('parse_error')
            
            # Parse outputs and calculate output revenue
            try:
                outputs = ast.literal_eval(row['outputs']) if row['outputs'] != '{}' else {}
                for good, quantity in outputs.items():
                    if good in self.goods_prices:
                        revenue = self.goods_prices[good] * quantity
                        pm_info['output_revenue'] += revenue
                        pm_info['output_goods'][good] = {
                            'quantity': quantity,
                            'price': self.goods_prices[good],
                            'total_revenue': revenue
                        }
                    else:
                        pm_info['missing_output_prices'].append(good)
            except:
                pm_info['missing_output_prices'].append('parse_error')
            
            # Calculate total profit
            pm_info['total_profit'] = pm_info['output_revenue'] - pm_info['input_cost']
            
            # Calculate profit per employee (avoid division by zero)
            if pm_info['total_employment'] != 0:
                pm_info['profit_per_employee'] = pm_info['total_profit'] / pm_info['total_employment']
            else:
                # If no employment, mark as unknown rather than infinite
                pm_info['profit_per_employee'] = None
                pm_info['employment_status'] = 'no_employment_data'
            
            results.append(pm_info)
        
        return pd.DataFrame(results)
    
    def get_summary_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get summary statistics of profitability analysis."""
        if df.empty:
            return {}
        
        # Filter out None values for statistics
        finite_profit = df[df['profit_per_employee'].notna()]
        
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
            'total_missing_input_prices': sum(len(pm['missing_input_prices']) for _, pm in df.iterrows()),
            'total_missing_output_prices': sum(len(pm['missing_output_prices']) for _, pm in df.iterrows()),
        }
        
        return stats
    
    def save_analysis(self, df: pd.DataFrame, output_path: str = "pm_profitability_analysis.csv") -> None:
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
    
    def print_top_profitable_pms(self, df: pd.DataFrame, top_n: int = 10) -> None:
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
        finite_df = df[df['profit_per_employee'].notna()]
        
        if not finite_df.empty:
            top_by_per_employee = finite_df.nlargest(top_n, 'profit_per_employee')
            print(f"\nBy Profit Per Employee:")
            for _, pm in top_by_per_employee.iterrows():
                print(f"{pm['production_method_name']:40} | Profit: {pm['total_profit']:8.1f} | Per Employee: {pm['profit_per_employee']:6.1f} | Employment: {pm['total_employment']:4}")

    def print_employment_analysis(self, df: pd.DataFrame) -> None:
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

def main():
    """Main function to run the profitability analysis."""
    print("=== Victoria 3 Production Methods Profitability Analysis ===\n")
    
    analyzer = PMProfitabilityAnalyzer()
    
    # Load data
    print("Loading goods prices...")
    analyzer.load_goods_prices()
    
    print("Loading production methods data...")
    analyzer.load_pm_data()
    
    # Calculate profitability
    print("Calculating profitability...")
    results_df = analyzer.calculate_pm_profitability()
    
    if not results_df.empty:
        # Get summary statistics
        stats = analyzer.get_summary_stats(results_df)
        
        print(f"\n=== SUMMARY STATISTICS ===")
        print(f"Total PMs analyzed: {stats['total_pms']}")
        print(f"Profitable PMs: {stats['profitable_pms']} ({stats['profitable_pms']/stats['total_pms']*100:.1f}%)")
        print(f"Unprofitable PMs: {stats['unprofitable_pms']} ({stats['unprofitable_pms']/stats['total_pms']*100:.1f}%)")
        print(f"Break-even PMs: {stats['break_even_pms']} ({stats['break_even_pms']/stats['total_pms']*100:.1f}%)")
        print(f"\nProfit Statistics:")
        print(f"  Average total profit: {stats['avg_total_profit']:.1f}")
        print(f"  Median total profit: {stats['median_total_profit']:.1f}")
        print(f"  Max total profit: {stats['max_total_profit']:.1f}")
        print(f"  Min total profit: {stats['min_total_profit']:.1f}")
        print(f"\nProfit Per Employee Statistics:")
        print(f"  Average profit per employee: {stats['avg_profit_per_employee']:.1f}")
        print(f"  Median profit per employee: {stats['median_profit_per_employee']:.1f}")
        print(f"  Max profit per employee: {stats['max_profit_per_employee']:.1f}")
        print(f"  Min profit per employee: {stats['min_profit_per_employee']:.1f}")
        print(f"\nMissing Price Data:")
        print(f"  Missing input prices: {stats['total_missing_input_prices']}")
        print(f"  Missing output prices: {stats['total_missing_output_prices']}")
        
        # Show employment analysis
        analyzer.print_employment_analysis(results_df)
        
        # Show top profitable PMs
        analyzer.print_top_profitable_pms(results_df, 15)
        
        # Save analysis
        print(f"\nSaving analysis...")
        analyzer.save_analysis(results_df)
        
    else:
        print("No results to analyze!")

if __name__ == "__main__":
    main() 