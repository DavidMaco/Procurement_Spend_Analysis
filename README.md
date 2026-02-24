# Procurement Spend Analysis & Supplier Optimization
### Strategic Cost Reduction for FMCG Manufacturing

A comprehensive data analytics project demonstrating procurement optimization strategies that identified **₦185.9 billion** (~$116M USD) in potential annual savings from ₦310.4 billion total procurement spend.

---

## 🎯 Project Overview

This portfolio project showcases advanced procurement analytics capabilities by analyzing 2 years of FMCG manufacturing procurement data across 2,500+ purchase orders, 40+ suppliers, and 4 major categories (Raw Materials, Packaging, Equipment, Services).

**Key Achievement**: Identified 59.9% cost reduction opportunity through data-driven procurement optimization.

---

## 💡 Business Problem

Manufacturing companies often struggle with:
- Price variance across suppliers for the same materials
- Supplier performance issues (late deliveries, quality problems)
- Lack of visibility into procurement spend patterns
- Maverick buying from non-approved suppliers
- Foreign exchange volatility impact

This project demonstrates how data analytics can uncover significant savings and risk mitigation opportunities.

---

## 📊 Key Findings

### Total Savings Identified: ₦185.9 Billion (59.9% of spend)

| Opportunity | Potential Savings | % of Spend | Impact |
|------------|-------------------|------------|---------|
| **Supplier Performance Improvement** | ₦167.5B | 53.95% | Replace poor performers with quality suppliers |
| **Price Standardization** | ₦18.5B | 5.95% | Negotiate better rates, consolidate purchases |
| **Maverick Buying Reduction** | ₦40.6B | 13.08% | Enforce approved supplier policy |

### Critical Insights:

1. **Price Variance**: Up to 24% price difference for identical materials across suppliers
2. **Late Deliveries**: 58.47% of orders delivered late, causing production delays
3. **Quality Issues**: 150 quality incidents costing ₦3.0 billion
4. **FX Risk**: 99.8% volatility in USD/NGN exchange rates affecting procurement costs
5. **Supplier Concentration**: Top 10 suppliers account for significant spend concentration

---

## 🛠️ Technical Stack

- **Database**: SQLite
- **Data Analysis**: Python (Pandas, NumPy)
- **Visualization**: Power BI, Matplotlib, Seaborn (upcoming)
- **Query Language**: SQL (Advanced queries with CTEs, window functions)

---

## 📁 Project Structure

```
procurement-analytics/
│
├── data/
│   ├── suppliers.csv           # Supplier master data
│   ├── materials.csv            # Materials master data
│   ├── purchase_orders.csv      # 2 years of PO transactions
│   └── quality_incidents.csv    # Quality incident tracking
│
├── database/
│   ├── procurement.db           # SQLite database
│   └── schema.sql               # Database schema (if using PostgreSQL)
│
├── analysis/
│   ├── generate_data.py         # Synthetic data generator
│   ├── create_db.py             # Database setup script
│   ├── analyze_procurement.py   # Main analysis script
│   └── analysis_queries.sql     # SQL analytical queries
│
├── insights/
│   └── procurement_insights.json # Key metrics and findings
│
├── visualizations/              # Power BI dashboards (upcoming)
│   └── procurement_dashboard.pbix
│
└── README.md
```

---

## 🔍 Analysis Methodology

### 1. Data Generation
Created realistic FMCG procurement dataset simulating:
- 40 suppliers across 4 categories (Raw Materials, Packaging, Equipment, Services)
- 71 unique materials with varying lead times and pricing
- 2,500 purchase orders over 24 months
- Realistic price variance, delivery delays, and quality incidents
- Multiple currencies (NGN, USD) with FX volatility

### 2. Database Design
- Normalized relational schema with referential integrity
- Analytical views for supplier performance, category spend, and savings opportunities
- Indexed tables for query optimization

### 3. SQL Analysis
Advanced SQL techniques employed:
- CTEs and subqueries for complex aggregations
- Window functions for ranking and running totals
- Date functions for time-series analysis
- Statistical aggregations (variance, percentiles)

### 4. Python Analytics
- Pandas for data manipulation and aggregation
- Statistical analysis for outlier detection
- Automated insights generation
- JSON export for dashboard integration

---

## 📈 Sample Insights

### Supplier Performance Scorecard
```sql
SELECT 
    supplier_name,
    total_orders,
    on_time_delivery_pct,
    quality_incidents,
    total_spend,
    performance_grade
FROM vw_supplier_performance
WHERE total_orders > 5
ORDER BY total_spend DESC;
```

### Price Variance Analysis
```sql
SELECT 
    material_name,
    MIN(unit_price) as best_price,
    AVG(unit_price) as avg_price,
    MAX(unit_price) as worst_price,
    (AVG(unit_price) - MIN(unit_price)) / MIN(unit_price) * 100 as overpayment_pct,
    SUM(total_amount) * (AVG(unit_price) - MIN(unit_price)) / AVG(unit_price) as potential_savings
FROM purchase_orders
GROUP BY material_name
HAVING overpayment_pct > 10
ORDER BY potential_savings DESC;
```

---

## 🎓 Skills Demonstrated

### Technical Skills:
- ✅ SQL (Advanced queries, views, indexing)
- ✅ Python (Pandas, NumPy, data manipulation)
- ✅ Database Design (normalization, relationships)
- ✅ Data Cleaning & Validation
- ✅ Statistical Analysis
- ✅ Data Visualization (upcoming Power BI dashboard)

### Domain Skills:
- ✅ Procurement Analytics
- ✅ Supplier Performance Management
- ✅ Cost Optimization Strategies
- ✅ Risk Analysis (FX, quality, delivery)
- ✅ Strategic Sourcing Recommendations

### Business Skills:
- ✅ Data-Driven Decision Making
- ✅ Stakeholder Communication (Executive-level insights)
- ✅ ROI Calculation
- ✅ Problem Identification & Solution Design

---

## 🚀 How to Run This Project

### Prerequisites
- Python 3.8+
- Pandas library
- SQLite (built into Python)

### Steps:
```bash
# 1. Clone repository
git clone https://github.com/yourusername/procurement-analytics.git
cd procurement-analytics

# 2. Generate synthetic data
python analysis/generate_data.py

# 3. Create database
python analysis/create_db.py

# 4. Run analysis
python analysis/analyze_procurement.py

# 5. View insights
cat insights/procurement_insights.json
```

---

## 📊 Next Steps (Coming Soon)

- [ ] Power BI Dashboard with interactive visualizations
- [ ] Predictive analytics for supplier risk scoring
- [ ] Machine learning model for price forecasting
- [ ] Automated reporting pipeline
- [ ] Integration with ERP systems (SAP, Oracle)

---

## 💼 Business Impact

If implemented in a real FMCG company with ₦310B annual procurement spend:

### Year 1 Savings Target: ₦50 Billion
- Price standardization: ₦18.5B (Quick win - 3-6 months)
- Top 5 supplier replacements: ₦31.5B (6-9 months)
- **ROI**: 400%+ on procurement optimization investment

### Year 2-3 Full Implementation: ₦185.9 Billion annually
- Complete supplier performance improvement
- Full category consolidation
- Maverick buying elimination
- **Impact**: 59.9% reduction in procurement costs

---

## 👨‍💼 About the Analyst

Chemical Engineering graduate with 5+ years procurement experience in FMCG manufacturing. Recently completed Data Analytics certification and building expertise in Data Engineering/Science.

**Core Competencies:**
- Procurement & Supply Chain Management
- Manufacturing Operations
- Data Analysis & Visualization
- SQL & Python Programming
- Business Intelligence

---

## 📫 Contact

- **LinkedIn**: [Your LinkedIn URL]
- **GitHub**: [Your GitHub Profile]
- **Email**: [Your Email]
- **Portfolio**: [Your Website]

---

## 📄 License

This project is for portfolio demonstration purposes. The data is synthetically generated and does not represent any real company.

---

## 🙏 Acknowledgments

Built as part of a portfolio project to demonstrate procurement analytics and data science capabilities for FMCG manufacturing optimization.

---

**⭐ If you found this project useful, please consider giving it a star!**
