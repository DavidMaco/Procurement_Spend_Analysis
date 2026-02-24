-- ============================================================================
-- PROCUREMENT SPEND ANALYSIS - SQL QUERIES
-- Portfolio Project: Strategic Insights for FMCG Cost Optimization
-- ============================================================================

-- ============================================================================
-- 1. EXECUTIVE SUMMARY METRICS
-- ============================================================================

-- Total Spend Overview
SELECT 
    COUNT(DISTINCT po_number) as total_orders,
    COUNT(DISTINCT supplier_id) as total_suppliers,
    ROUND(SUM(total_amount_ngn), 0) as total_spend_ngn,
    ROUND(AVG(total_amount_ngn), 0) as avg_order_value,
    ROUND(SUM(CASE WHEN currency = 'USD' THEN total_amount_usd ELSE 0 END), 0) as total_usd_spend
FROM purchase_orders;

-- ============================================================================
-- 2. SPEND BY CATEGORY (Pareto Analysis)
-- ============================================================================

SELECT 
    category,
    COUNT(*) as order_count,
    ROUND(SUM(total_amount_ngn), 0) as total_spend,
    ROUND(SUM(total_amount_ngn) * 100.0 / (SELECT SUM(total_amount_ngn) FROM purchase_orders), 2) as pct_of_total,
    ROUND(AVG(total_amount_ngn), 0) as avg_order_value,
    COUNT(DISTINCT supplier_id) as supplier_count
FROM purchase_orders
GROUP BY category
ORDER BY total_spend DESC;

-- ============================================================================
-- 3. SUPPLIER CONCENTRATION RISK
-- ============================================================================

-- Top 10 suppliers by spend (check for over-dependence)
SELECT 
    supplier_name,
    category,
    country,
    COUNT(*) as order_count,
    ROUND(SUM(total_amount_ngn), 0) as total_spend,
    ROUND(SUM(total_amount_ngn) * 100.0 / (SELECT SUM(total_amount_ngn) FROM purchase_orders), 2) as pct_of_total_spend
FROM purchase_orders
GROUP BY supplier_name, category, country
ORDER BY total_spend DESC
LIMIT 10;

-- ============================================================================
-- 4. PRICE VARIANCE ANALYSIS (Potential Savings)
-- ============================================================================

-- Find materials where we're paying different prices to different suppliers
SELECT 
    po.material_name,
    po.category,
    COUNT(DISTINCT po.supplier_id) as supplier_count,
    ROUND(MIN(po.unit_price_ngn), 2) as min_price,
    ROUND(AVG(po.unit_price_ngn), 2) as avg_price,
    ROUND(MAX(po.unit_price_ngn), 2) as max_price,
    ROUND((MAX(po.unit_price_ngn) - MIN(po.unit_price_ngn)) / MIN(po.unit_price_ngn) * 100, 2) as price_variance_pct,
    ROUND(SUM(po.total_amount_ngn) * (AVG(po.unit_price_ngn) - MIN(po.unit_price_ngn)) / AVG(po.unit_price_ngn), 0) as potential_savings_ngn
FROM purchase_orders po
GROUP BY po.material_name, po.category
HAVING COUNT(DISTINCT po.supplier_id) > 1 AND price_variance_pct > 10
ORDER BY potential_savings_ngn DESC
LIMIT 20;

-- ============================================================================
-- 5. SUPPLIER PERFORMANCE SCORECARD
-- ============================================================================

SELECT 
    supplier_name,
    category,
    country,
    total_orders,
    ROUND(total_spend_ngn, 0) as total_spend,
    ROUND(on_time_delivery_pct, 2) as otd_pct,
    quality_incidents,
    ROUND(total_quality_cost, 0) as quality_cost,
    CASE 
        WHEN on_time_delivery_pct >= 90 AND quality_incidents = 0 THEN 'A - Excellent'
        WHEN on_time_delivery_pct >= 80 AND quality_incidents <= 2 THEN 'B - Good'
        WHEN on_time_delivery_pct >= 70 OR quality_incidents <= 5 THEN 'C - Average'
        ELSE 'D - Poor'
    END as performance_grade
FROM vw_supplier_performance
WHERE total_orders > 5
ORDER BY total_spend DESC;

-- ============================================================================
-- 6. DELIVERY PERFORMANCE ANALYSIS
-- ============================================================================

-- Late delivery trends by supplier
SELECT 
    supplier_name,
    category,
    COUNT(*) as total_deliveries,
    SUM(CASE WHEN actual_delivery_date > expected_delivery_date THEN 1 ELSE 0 END) as late_deliveries,
    ROUND(SUM(CASE WHEN actual_delivery_date > expected_delivery_date THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as late_delivery_pct,
    ROUND(AVG(JULIANDAY(actual_delivery_date) - JULIANDAY(expected_delivery_date)), 1) as avg_delay_days
FROM purchase_orders
WHERE actual_delivery_date IS NOT NULL
GROUP BY supplier_name, category
HAVING total_deliveries > 5
ORDER BY late_delivery_pct DESC
LIMIT 15;

-- ============================================================================
-- 7. PAYMENT TERMS OPTIMIZATION
-- ============================================================================

-- Analyze payment terms vs actual payment performance
SELECT 
    s.payment_terms,
    COUNT(*) as order_count,
    ROUND(SUM(po.total_amount_ngn), 0) as total_value,
    SUM(CASE WHEN po.payment_status = 'Paid' THEN 1 ELSE 0 END) as paid_count,
    SUM(CASE WHEN po.payment_status = 'Overdue' THEN 1 ELSE 0 END) as overdue_count,
    ROUND(SUM(CASE WHEN po.payment_status = 'Overdue' THEN po.total_amount_ngn ELSE 0 END), 0) as overdue_value
FROM purchase_orders po
JOIN suppliers s ON po.supplier_id = s.supplier_id
GROUP BY s.payment_terms
ORDER BY total_value DESC;

-- ============================================================================
-- 8. FOREIGN EXCHANGE EXPOSURE ANALYSIS
-- ============================================================================

-- USD spend and FX risk
SELECT 
    strftime('%Y-%m', po_date) as month,
    COUNT(*) as usd_orders,
    ROUND(SUM(total_amount_usd), 0) as total_usd,
    ROUND(AVG(total_amount_ngn / NULLIF(total_amount_usd, 0)), 2) as avg_fx_rate,
    ROUND(MIN(total_amount_ngn / NULLIF(total_amount_usd, 0)), 2) as min_fx_rate,
    ROUND(MAX(total_amount_ngn / NULLIF(total_amount_usd, 0)), 2) as max_fx_rate,
    ROUND((MAX(total_amount_ngn / NULLIF(total_amount_usd, 0)) - MIN(total_amount_ngn / NULLIF(total_amount_usd, 0))) / 
          MIN(total_amount_ngn / NULLIF(total_amount_usd, 0)) * 100, 2) as fx_volatility_pct
FROM purchase_orders
WHERE currency = 'USD' AND total_amount_usd > 0
GROUP BY month
ORDER BY month;

-- ============================================================================
-- 9. QUALITY COST ANALYSIS
-- ============================================================================

-- Quality incidents impact by supplier
SELECT 
    s.supplier_name,
    s.category,
    s.quality_rating,
    COUNT(qi.incident_id) as incident_count,
    SUM(CASE WHEN qi.severity = 'High' THEN 1 ELSE 0 END) as high_severity_count,
    ROUND(SUM(qi.cost_impact_ngn), 0) as total_quality_cost,
    ROUND(SUM(qi.cost_impact_ngn) * 100.0 / sp.total_spend_ngn, 2) as quality_cost_pct_of_spend
FROM quality_incidents qi
JOIN suppliers s ON qi.supplier_id = s.supplier_id
JOIN vw_supplier_performance sp ON s.supplier_id = sp.supplier_id
GROUP BY s.supplier_name, s.category, s.quality_rating
ORDER BY total_quality_cost DESC;

-- ============================================================================
-- 10. MAVERICK BUYING ANALYSIS
-- ============================================================================

-- Orders from non-approved or high-risk suppliers
SELECT 
    po.supplier_name,
    s.risk_level,
    s.is_approved,
    COUNT(*) as order_count,
    ROUND(SUM(po.total_amount_ngn), 0) as total_spend,
    GROUP_CONCAT(DISTINCT po.buyer) as buyers
FROM purchase_orders po
JOIN suppliers s ON po.supplier_id = s.supplier_id
WHERE s.is_approved = 0 OR s.risk_level = 'High'
GROUP BY po.supplier_name, s.risk_level, s.is_approved
ORDER BY total_spend DESC;

-- ============================================================================
-- 11. SPEND TREND ANALYSIS (Monthly)
-- ============================================================================

SELECT 
    strftime('%Y', po_date) as year,
    strftime('%m', po_date) as month,
    category,
    COUNT(*) as order_count,
    ROUND(SUM(total_amount_ngn), 0) as total_spend,
    ROUND(AVG(total_amount_ngn), 0) as avg_order_value
FROM purchase_orders
GROUP BY year, month, category
ORDER BY year, month, category;

-- ============================================================================
-- 12. SAVINGS OPPORTUNITIES SUMMARY
-- ============================================================================

-- Consolidate all identified savings opportunities
SELECT 
    'Price Standardization' as opportunity_type,
    COUNT(*) as opportunities,
    ROUND(SUM(potential_savings_ngn), 0) as total_potential_savings
FROM vw_savings_opportunities
UNION ALL
SELECT 
    'Quality Cost Reduction' as opportunity_type,
    COUNT(DISTINCT supplier_id) as opportunities,
    ROUND(SUM(total_quality_cost), 0) as total_potential_savings
FROM vw_supplier_performance
WHERE quality_incidents > 0
UNION ALL
SELECT 
    'Supplier Consolidation' as opportunity_type,
    COUNT(DISTINCT category) as opportunities,
    ROUND(SUM(total_spend) * 0.05, 0) as estimated_savings  -- Assume 5% savings from consolidation
FROM (
    SELECT category, SUM(total_amount_ngn) as total_spend
    FROM purchase_orders
    GROUP BY category
    HAVING COUNT(DISTINCT supplier_id) > 10
);

-- ============================================================================
-- 13. TOP 10 ACTION ITEMS (For Executive Presentation)
-- ============================================================================

-- Suppliers to renegotiate
SELECT 
    'Renegotiate Price' as action_item,
    supplier_name as target,
    category,
    ROUND(potential_savings_ngn, 0) as estimated_savings,
    'High price variance detected' as reason
FROM vw_savings_opportunities
ORDER BY potential_savings_ngn DESC
LIMIT 5

UNION ALL

-- Suppliers to replace due to poor performance
SELECT 
    'Replace Supplier' as action_item,
    supplier_name as target,
    category,
    ROUND(total_quality_cost + (total_spend_ngn * 0.03), 0) as estimated_savings,
    'Poor delivery & quality performance' as reason
FROM vw_supplier_performance
WHERE on_time_delivery_pct < 70 AND quality_incidents > 3
ORDER BY total_spend_ngn DESC
LIMIT 5;
