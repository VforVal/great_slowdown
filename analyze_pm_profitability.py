#!/usr/bin/env python3
"""
Script to analyze Victoria 3 production methods profitability.
Combines PM data with goods prices to calculate total profitability and profitability per employee.
"""

from pm_analysis.loader import load_goods_prices, load_pm_data
from pm_analysis.calculator import calculate_pm_profitability
from pm_analysis.reporter import get_summary_stats, print_employment_analysis, print_top_profitable_pms, save_analysis

def main():
    """Main function to run the profitability analysis."""
    print("=== Victoria 3 Production Methods Profitability Analysis ===\n")
    
    # Load data
    print("Loading goods prices...")
    goods_prices = load_goods_prices()
    
    print("Loading production methods data...")
    pm_data = load_pm_data()
    
    # Calculate profitability
    print("Calculating profitability...")
    results_df = calculate_pm_profitability(pm_data, goods_prices)
    
    if not results_df.empty:
        # Get summary statistics
        stats = get_summary_stats(results_df)
        
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
        print_employment_analysis(results_df)
        
        # Show top profitable PMs
        print_top_profitable_pms(results_df, 15)
        
        # Save analysis
        print(f"\nSaving analysis...")
        save_analysis(results_df)
        
    else:
        print("No results to analyze!")

if __name__ == "__main__":
    main() 