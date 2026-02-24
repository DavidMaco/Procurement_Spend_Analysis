"""
Procurement Spend Analysis - Python Analysis Script
Generates key insights and identifies savings opportunities
"""

import pandas as pd
import sqlite3
import json

from optimization_engine import run_supplier_optimization
from scenario_analysis import run_sensitivity_analysis
from constrained_optimization import run_constrained_optimization
from monte_carlo import run_monte_carlo_analysis, monte_carlo_to_dataframe

def run_analysis():
    """Run comprehensive procurement analysis"""
    
    # Connect to database
    conn = sqlite3.connect('procurement.db')

    with open('scenario_assumptions.json', 'r') as f:
        assumptions = json.load(f)
    
    print("=" * 80)
    print("PROCUREMENT SPEND ANALYSIS & SUPPLIER OPTIMIZATION")
    print("Strategic Insights for Cost Reduction")
    print("=" * 80)
    
    insights = {}
    
    # 1. Executive Summary
    print("\n[EXEC] EXECUTIVE SUMMARY")
    print("-" * 80)
    
    exec_summary = pd.read_sql('''
        SELECT 
            COUNT(DISTINCT po_number) as total_orders,
            COUNT(DISTINCT supplier_id) as total_suppliers,
            ROUND(SUM(total_amount_ngn), 0) as total_spend_ngn,
            ROUND(AVG(total_amount_ngn), 0) as avg_order_value
        FROM purchase_orders
    ''', conn)
    
    total_spend = exec_summary['total_spend_ngn'].values[0]
    print(f"Total Spend (2 years): NGN {total_spend:,.0f}")
    print(f"Total Orders: {exec_summary['total_orders'].values[0]:,}")
    print(f"Active Suppliers: {exec_summary['total_suppliers'].values[0]}")
    print(f"Average Order Value: NGN {exec_summary['avg_order_value'].values[0]:,.0f}")
    
    insights['total_spend'] = float(total_spend)
    
    # 2. Spend by Category (Pareto Analysis)
    print("\n[PARETO] SPEND BY CATEGORY (Pareto Analysis)")
    print("-" * 80)
    
    category_spend = pd.read_sql('''
        SELECT 
            category,
            ROUND(SUM(total_amount_ngn), 0) as total_spend,
            ROUND(SUM(total_amount_ngn) * 100.0 / (SELECT SUM(total_amount_ngn) FROM purchase_orders), 2) as pct_of_total
        FROM purchase_orders
        GROUP BY category
        ORDER BY total_spend DESC
    ''', conn)
    
    print(category_spend.to_string(index=False))
    
    # 3. Top Savings Opportunity: Price Standardization
    print("\n[SAVINGS1] Price Standardization")
    print("-" * 80)
    
    price_variance = pd.read_sql('''
        SELECT 
            material_name,
            category,
            COUNT(DISTINCT supplier_id) as supplier_count,
            ROUND(MIN(unit_price_ngn), 2) as min_price,
            ROUND(AVG(unit_price_ngn), 2) as avg_price,
            ROUND(MAX(unit_price_ngn), 2) as max_price,
            ROUND((AVG(unit_price_ngn) - MIN(unit_price_ngn)) / MIN(unit_price_ngn) * 100, 2) as overpayment_pct,
            ROUND(SUM(total_amount_ngn) * (AVG(unit_price_ngn) - MIN(unit_price_ngn)) / AVG(unit_price_ngn), 0) as potential_savings
        FROM purchase_orders
        GROUP BY material_name, category
        HAVING supplier_count > 1 AND overpayment_pct > 10
        ORDER BY potential_savings DESC
        LIMIT 10
    ''', conn)
    
    total_price_savings = price_variance['potential_savings'].sum()
    print(f"\nIdentified {len(price_variance)} items with significant price variance")
    print(f"TOTAL POTENTIAL SAVINGS: NGN {total_price_savings:,.0f}\n")
    print("Top 5 Opportunities:")
    print(price_variance[['material_name', 'overpayment_pct', 'potential_savings']].head().to_string(index=False))
    
    insights['price_standardization_savings'] = float(total_price_savings)
    
    # 4. Supplier Performance Issues
    print("\n[ALERT] Supplier Performance Improvement")
    print("-" * 80)
    
    poor_performers = pd.read_sql('''
        SELECT 
            supplier_name,
            category,
            total_orders,
            ROUND(on_time_delivery_pct, 2) as otd_pct,
            quality_incidents,
            ROUND(total_quality_cost, 0) as quality_cost,
            ROUND(total_spend_ngn, 0) as total_spend
        FROM vw_supplier_performance
        WHERE (on_time_delivery_pct < 80 OR quality_incidents > 2) AND total_orders > 5
        ORDER BY total_spend DESC
        LIMIT 10
    ''', conn)
    
    quality_cost = poor_performers['quality_cost'].sum()
    # Estimate 3-5% additional cost from late deliveries (rush orders, production delays)
    delivery_cost = poor_performers['total_spend'].sum() * 0.03
    total_performance_savings = quality_cost + delivery_cost
    
    print(f"\nIdentified {len(poor_performers)} underperforming suppliers")
    print(f"Quality Cost Impact: NGN {quality_cost:,.0f}")
    print(f"Estimated Late Delivery Cost: NGN {delivery_cost:,.0f}")
    print(f"TOTAL POTENTIAL SAVINGS: NGN {total_performance_savings:,.0f}\n")
    print("Top 5 Poor Performers:")
    print(poor_performers[['supplier_name', 'otd_pct', 'quality_incidents', 'total_spend']].head().to_string(index=False))
    
    insights['performance_improvement_savings'] = float(total_performance_savings)
    
    # 5. Supplier Consolidation Opportunity
    print("\n[CONSOLIDATE] Supplier Consolidation")
    print("-" * 80)
    
    fragmentation = pd.read_sql('''
        SELECT 
            category,
            COUNT(DISTINCT supplier_id) as supplier_count,
            ROUND(SUM(total_amount_ngn), 0) as total_spend,
            ROUND(SUM(total_amount_ngn) / COUNT(DISTINCT supplier_id), 0) as spend_per_supplier
        FROM purchase_orders
        GROUP BY category
        HAVING supplier_count > 8
        ORDER BY total_spend DESC
    ''', conn)
    
    # Assume 5-7% savings from consolidation (better pricing, reduced admin)
    consolidation_savings = fragmentation['total_spend'].sum() * 0.06
    
    print(f"\n{len(fragmentation)} categories have high supplier fragmentation")
    print(f"POTENTIAL SAVINGS (6% from consolidation): NGN {consolidation_savings:,.0f}\n")
    print(fragmentation.to_string(index=False))
    
    insights['consolidation_savings'] = float(consolidation_savings)
    
    # 6. Maverick Buying
    print("\n[RISK] Maverick Buying (Non-Approved/High-Risk Suppliers)")
    print("-" * 80)
    
    maverick = pd.read_sql('''
        SELECT 
            po.supplier_name,
            s.risk_level,
            COUNT(*) as order_count,
            ROUND(SUM(po.total_amount_ngn), 0) as total_spend
        FROM purchase_orders po
        JOIN suppliers s ON po.supplier_id = s.supplier_id
        WHERE s.is_approved = 0 OR s.risk_level = 'High'
        GROUP BY po.supplier_name, s.risk_level
        ORDER BY total_spend DESC
    ''', conn)
    
    maverick_spend = maverick['total_spend'].sum()
    print(f"\nTotal Maverick Spend: NGN {maverick_spend:,.0f}")
    print(f"({maverick_spend/total_spend*100:.2f}% of total procurement)\n")
    if len(maverick) > 0:
        print(maverick.head(10).to_string(index=False))
    
    insights['maverick_spend'] = float(maverick_spend)
    
    # 7. FX Risk
    print("\n[FX] FOREIGN EXCHANGE EXPOSURE")
    print("-" * 80)
    
    fx_exposure = pd.read_sql('''
        SELECT 
            ROUND(SUM(total_amount_usd), 0) as total_usd_spend,
            ROUND(AVG(total_amount_ngn / NULLIF(total_amount_usd, 0)), 2) as avg_fx_rate,
            ROUND(MIN(total_amount_ngn / NULLIF(total_amount_usd, 0)), 2) as min_fx_rate,
            ROUND(MAX(total_amount_ngn / NULLIF(total_amount_usd, 0)), 2) as max_fx_rate
        FROM purchase_orders
        WHERE currency = 'USD' AND total_amount_usd > 0
    ''', conn)
    
    if len(fx_exposure) > 0 and fx_exposure['total_usd_spend'].values[0]:
        usd_spend = fx_exposure['total_usd_spend'].values[0]
        fx_volatility = (fx_exposure['max_fx_rate'].values[0] - fx_exposure['min_fx_rate'].values[0]) / fx_exposure['min_fx_rate'].values[0] * 100
        
        print(f"Total USD Spend: ${usd_spend:,.0f}")
        print(f"FX Rate Range: NGN {fx_exposure['min_fx_rate'].values[0]:,.2f} - NGN {fx_exposure['max_fx_rate'].values[0]:,.2f}")
        print(f"FX Volatility: {fx_volatility:.1f}%")
        
        insights['usd_spend'] = float(usd_spend)
        insights['fx_volatility'] = float(fx_volatility)
    
    # 8. TOTAL SAVINGS SUMMARY
    print("\n" + "=" * 80)
    print("[TOP] TOTAL IDENTIFIED SAVINGS OPPORTUNITIES")
    print("=" * 80)
    
    total_savings = total_price_savings + total_performance_savings + consolidation_savings
    
    savings_summary = pd.DataFrame({
        'Opportunity': [
            'Price Standardization',
            'Supplier Performance Improvement',
            'Supplier Consolidation',
            'TOTAL SAVINGS POTENTIAL'
        ],
        'Potential Savings (NGN)': [
            f'{total_price_savings:,.0f}',
            f'{total_performance_savings:,.0f}',
            f'{consolidation_savings:,.0f}',
            f'{total_savings:,.0f}'
        ],
        '% of Total Spend': [
            f'{total_price_savings/total_spend*100:.2f}%',
            f'{total_performance_savings/total_spend*100:.2f}%',
            f'{consolidation_savings/total_spend*100:.2f}%',
            f'{total_savings/total_spend*100:.2f}%'
        ]
    })
    
    print(savings_summary.to_string(index=False))
    
    print(f"\n[GOAL] TARGET: Achieve NGN {total_savings:,.0f} in annual savings")
    print(f"       This represents {total_savings/total_spend*100:.1f}% reduction in procurement costs")
    
    insights['total_savings'] = float(total_savings)
    insights['savings_percentage'] = float(total_savings/total_spend*100)

    # 9. Decision Optimization (Supplier Allocation)
    print("\n[PHASE1] PHASE 1 - SUPPLIER OPTIMIZATION")
    print("-" * 80)

    optimization_cfg = assumptions.get('supplier_optimization', {})
    optimization_df, optimization_summary = run_supplier_optimization(
        conn=conn,
        max_suppliers_per_category=int(optimization_cfg.get('max_suppliers_per_category', 3)),
        min_supplier_share=float(optimization_cfg.get('min_supplier_share', 0.15)),
        score_weights=optimization_cfg.get('score_weights', None),
    )

    if not optimization_df.empty:
        optimization_df.to_csv('supplier_optimization_recommendations.csv', index=False)
        print(f"Recommended allocations generated: {len(optimization_df):,} rows")
        print(
            f"Estimated optimization savings: NGN {optimization_summary['optimization_savings_ngn']:,.0f} "
            f"({optimization_summary['optimization_savings_pct']:.2f}% of historical spend baseline)"
        )
    else:
        print("No optimization recommendations generated from current data.")

    insights['optimization_savings'] = float(optimization_summary.get('optimization_savings_ngn', 0.0))
    insights['optimization_savings_pct'] = float(optimization_summary.get('optimization_savings_pct', 0.0))

    # 10. Sensitivity Analysis
    print("\n[SCENARIO] Sensitivity Analysis: Conservative to Aggressive")
    print("-" * 80)

    sensitivity_df = run_sensitivity_analysis(
        insights=insights,
        scenario_factors=assumptions.get('sensitivity_scenarios', {}),
    )
    sensitivity_df.to_csv('savings_scenarios.csv', index=False)
    print(sensitivity_df.to_string(index=False))
    
    # 11. Constrained Optimization (Phase 2)
    print("\n[PHASE2] PHASE 2 - CONSTRAINED OPTIMIZATION: SLA-Enforced Allocation")
    print("-" * 80)
    constraints_cfg = assumptions.get('constraints', {}).get('standard', {})
    constrained_recs_df, constrained_summary = run_constrained_optimization(
        conn=conn,
        constraints=constraints_cfg,
    )
    constrained_recs_df.to_csv('constrained_supplier_recommendations.csv', index=False)
    print(f"Constrained savings: NGN {constrained_summary['constrained_savings_ngn']:.2f}B "
          f"({constrained_summary['constrained_savings_pct']:.1f}% of spend)")
    print(f"Dual-sourced categories: {constrained_summary['dual_sourced_categories']}")
    
    insights['constrained_savings_ngn'] = constrained_summary['constrained_savings_ngn']
    insights['constrained_savings_pct'] = constrained_summary['constrained_savings_pct']
    insights['constrained_dual_sourced_count'] = constrained_summary['dual_sourced_categories']
    
    # 12. Monte Carlo Uncertainty (Phase 2)
    print("\n[PHASE2] PHASE 2 - MONTE CARLO UNCERTAINTY: 10,000 Simulation Runs")
    print("-" * 80)
    mc_cfg = assumptions.get('monte_carlo', {})
    mc_results = run_monte_carlo_analysis(
        base_insights=insights,
        num_simulations=mc_cfg.get('num_simulations', 10000),
        random_seed=mc_cfg.get('random_seed', 42),
        uncertainty_params=mc_cfg.get('uncertainty_parameters', {}),
    )
    mc_df = monte_carlo_to_dataframe(mc_results)
    mc_df.to_csv('monte_carlo_uncertainty_bounds.csv', index=False)
    print(mc_df.to_string(index=False))
    print(f"\nSavings confidence interval (NGN): "
          f"[{mc_results['total_savings_p05_ngn']:,.0f}, {mc_results['total_savings_p95_ngn']:,.0f}]")
    
    insights.update(mc_results)
    
    # Save insights to JSON
    with open('procurement_insights.json', 'w') as f:
        json.dump(insights, f, indent=2)
    
    print("\n" + "=" * 80)
    print("[OK] Analysis complete! Insights saved to procurement_insights.json")
    print("=" * 80)
    
    conn.close()
    
    return insights

if __name__ == "__main__":
    insights = run_analysis()
