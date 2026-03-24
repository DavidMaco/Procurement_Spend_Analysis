# Aegis Procurement Intelligence Platform

## Complete Project Documentation

---

## Table of Contents

1. [What Is This Project?](#1-what-is-this-project)
2. [The Problem We Solve](#2-the-problem-we-solve)
3. [How We Solve It — The Big Picture](#3-how-we-solve-it--the-big-picture)
4. [Business Questions This Platform Answers](#4-business-questions-this-platform-answers)
5. [Decisions You Can Make With This](#5-decisions-you-can-make-with-this)
6. [How Everything Works — A Plain-English Walkthrough](#6-how-everything-works--a-plain-english-walkthrough)
7. [Step-by-Step Project Walkthrough](#7-step-by-step-project-walkthrough)
8. [The Technology Behind It](#8-the-technology-behind-it)
9. [Dashboard Pages — What Each Screen Shows](#9-dashboard-pages--what-each-screen-shows)
10. [The SaaS Platform Layer](#10-the-saas-platform-layer)
11. [Infrastructure & Deployment](#11-infrastructure--deployment)
12. [Security, Compliance & Audit](#12-security-compliance--audit)
13. [Testing & Quality Assurance](#13-testing--quality-assurance)
14. [Key Numbers & Results](#14-key-numbers--results)
15. [Glossary — Terms Explained Simply](#15-glossary--terms-explained-simply)

---

## 1. What Is This Project?

**Aegis Procurement Intelligence Platform** is a software system that helps companies understand, control, and optimize how they spend money buying things from suppliers.

Think of it this way: every large company buys thousands of items — raw materials, packaging, equipment, services — from hundreds of different suppliers. That spending can easily reach billions of naira (or dollars) per year. Without a system to analyze it, companies overpay for products, work with unreliable suppliers, miss bulk discount opportunities, and expose themselves to financial risk — all without even knowing it.

This platform takes a company's purchasing data (which is usually scattered across spreadsheets, ERP systems like SAP or Oracle, and filing cabinets) and transforms it into **clear, actionable intelligence** — dashboards, alerts, recommendations, risk scores, and savings opportunities — so that procurement leaders can make smarter decisions backed by data rather than gut instinct.

What makes this project unique:

- It is not just a report or a dashboard. It is a **complete intelligence engine** — it generates data, validates it, analyzes it, runs mathematical optimization, simulates uncertainty with 10,000 scenarios, and produces specific recommendations on which suppliers to use and how much to allocate to each.
- It is built as a **multi-tenant SaaS platform** — meaning multiple companies can each use it simultaneously, with their data completely isolated from each other, and with a billing and subscription system built in.
- It includes **AI-powered anomaly detection and demand forecasting** — the system uses machine learning to automatically spot unusual spending patterns and predict future demand.
- It has a **full audit trail** — every recommendation the system makes, and every approval or rejection by a human, is permanently recorded in a tamper-evident log with integrity verification.

---

## 2. The Problem We Solve

### The Everyday Reality of Procurement

Imagine you run a large factory that makes consumer goods (soap, food, beverages). Every month, your team places hundreds of purchase orders: buying palm oil from Supplier A, plastic bottles from Supplier B, cardboard boxes from Supplier C, and so on.

Here is what typically goes wrong:

### Problem 1: "We're paying different prices for the same thing"

Your Lagos office buys palm oil from Supplier A at ₦850 per kilogram. Your Kano office buys the exact same palm oil from Supplier B at ₦1,100 per kilogram. Nobody realizes this because the information is in separate spreadsheets. **That's a 29% price gap that nobody knows about.**

> **This is called Price Variance.** Our platform detects it automatically, flags it, and calculates exactly how much money you'd save if every office paid the lowest available price.

### Problem 2: "Suppliers keep delivering late, and it's costing us money"

Supplier C has a contract to deliver within 14 days. But over the last 6 months, they've delivered late 40% of the time. Each late delivery forces your production line to stop, costing ₦5 million per incident. Nobody has connected the dots because delivery data is in one system and production cost data is in another.

> **This is called Supplier Performance Analysis.** Our platform scores every supplier on delivery reliability, quality, and cost — then recommends whether to keep, replace, or renegotiate with them.

### Problem 3: "We use too many suppliers for the same category"

Your company buys packaging materials from 12 different suppliers. If you consolidated down to 3 or 4, you could negotiate volume discounts of 6-10%. But nobody has done the analysis to figure out which 3 or 4 to keep.

> **This is called Supplier Consolidation.** Our platform uses mathematical optimization (the same kind of math used to route airline flights) to determine the best combination of suppliers that minimizes total cost while maintaining supply security.

### Problem 4: "Someone is buying from unapproved suppliers"

Your procurement policy says you should only buy from pre-approved, vetted suppliers. But 13% of your total spending is going to suppliers that haven't been formally approved — a practice known as maverick buying. This exposes the company to quality risk, fraud risk, and compliance violations.

> **This is called Maverick Spend Detection.** Our platform flags every purchase order placed with a non-approved or high-risk supplier.

### Problem 5: "We don't know how much we could realistically save"

The CFO asks: "If we implement all your recommendations, how much will we save?" The honest answer is: "It depends." Prices fluctuate. Suppliers may not agree to your terms. Some savings estimates are conservative; others are aggressive. Nobody has quantified the range of possible outcomes.

> **This is called Uncertainty Quantification.** Our platform runs 10,000 simulated scenarios (Monte Carlo simulation) to give you a confidence interval: "We are 90% confident savings will be between ₦150 billion and ₦225 billion."

### Problem 6: "We have no record of who approved what"

A recommendation was made to switch from Supplier X to Supplier Y. Six months later, Supplier Y has quality issues and someone asks: "Who approved that switch? What data was it based on? When was it decided?" Nobody has a clear, integrity-verifiable record.

> **This is the Audit Trail problem.** Our platform records every recommendation, every approval, every rejection — in a permanent, hash-chained ledger where tampering is detectable through integrity verification.

---

## 3. How We Solve It — The Big Picture

The platform works in five stages, like an assembly line:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                                                                          │
│   STAGE 1          STAGE 2           STAGE 3           STAGE 4          │
│   ────────         ────────          ────────           ────────         │
│                                                                          │
│   Get the    →    Clean &     →    Analyze &     →    Optimize &        │
│   Data            Validate         Measure             Recommend        │
│                                                                          │
│   • Upload CSV    • Map columns    • Calculate KPIs   • MILP solver     │
│   • Generate      • Fill gaps      • Score suppliers   • Constraints    │
│     synthetic     • Type-check     • Find anomalies    • Scenarios      │
│   • Connect ERP   • Reconcile      • Detect risk       • Monte Carlo   │
│                                                                          │
│                                                                          │
│   STAGE 5                                                                │
│   ────────                                                               │
│                                                                          │
│   Present &                                                              │
│   Act                                                                    │
│                                                                          │
│   • Interactive dashboards (Streamlit)                                   │
│   • Executive reports (Power BI)                                         │
│   • REST API for other systems                                           │
│   • Real-time alerts & notifications                                     │
│   • Approval workflow & audit log                                        │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Stage 1: Get the Data

The platform accepts data in three ways:
- **Upload your own CSV files** — procurement data from SAP, Oracle, Coupa, or a spreadsheet
- **Use the built-in demo dataset** — 2,500 realistic purchase orders pre-generated for demonstration
- **Generate fresh synthetic data** — create a new random-but-realistic dataset on demand

### Stage 2: Clean & Validate

Real-world data is messy. Different companies call the same column different things ("vendor_id" vs. "supplier_id" vs. "supplier_code"). Some rows have missing values. Some have impossible values (negative quantities, delivery dates before order dates).

The platform automatically:
- **Maps columns** to a standard format (recognizes 50+ column name variations)
- **Fills gaps** with sensible defaults
- **Type-checks** everything (dates are dates, numbers are numbers)
- **Reconciles** financial totals (does quantity × price = total amount?)
- **Flags** data quality issues so you know what to fix at source

### Stage 3: Analyze & Measure

Once the data is clean, the platform computes hundreds of metrics:
- **Spend distribution** — where money goes (by category, supplier, time period)
- **Supplier scorecards** — each supplier graded A through E based on delivery, quality, cost
- **Price variance** — which materials have the biggest gap between highest and lowest prices paid
- **Risk exposure** — how much spending is with risky, unapproved, or single-source suppliers
- **Quality impact** — how much defects and contamination are costing you

### Stage 4: Optimize & Recommend

This is where the math gets powerful. The platform doesn't just show you problems — it tells you exactly what to do about them, using three levels of increasingly sophisticated analysis:

**Level 1 — Supplier Optimization (Mathematical Programming):**
A mathematical solver evaluates every possible combination of suppliers per category and finds the allocation that minimizes total cost while balancing delivery speed, quality, and risk. Think of it like a GPS finding the fastest route through traffic — except instead of roads, it's evaluating suppliers.

**Level 2 — Constrained Optimization (Policy-Aware):**
The same solver but with real-world business rules applied: "No single supplier can have more than 50% of a category." "Only use suppliers with 85%+ on-time delivery." "High-risk suppliers are excluded." This makes the recommendations implementable in the real world.

**Level 3 — Monte Carlo Simulation (Uncertainty-Aware):**
The platform runs 10,000 random simulations, each with slightly different assumptions (prices vary ±15%, delivery performance varies ±20%, consolidation savings vary ±25%), to give you a probability distribution of outcomes. Instead of a single number, you get: "We're 90% confident savings will be between X and Y."

### Stage 5: Present & Act

Results are delivered through:
- **8 interactive dashboard pages** (Streamlit web app) — for daily use by analysts and managers
- **Power BI export pack** — for executives who prefer Microsoft's reporting tool
- **REST API** (20+ endpoints) — for integrating with other company systems
- **Real-time alerts** — when KPIs deviate from baseline
- **Approval workflow** — recommendations go through a formal approve/reject process with full audit trail

---

## 4. Business Questions This Platform Answers

Here are the specific questions a procurement leader, CFO, or supply chain manager can answer using this platform:

### Spend Visibility
| # | Question | Where to Find the Answer |
|---|----------|--------------------------|
| 1 | **Where does our money go?** Which categories consume the most budget? | Executive Overview dashboard — Spend by Category chart |
| 2 | **Who are our top suppliers by spend?** Are we over-concentrating? | Supplier Performance dashboard — Top 15 Suppliers chart |
| 3 | **How has spending changed over time?** Is it growing, shrinking, or seasonal? | Executive Overview — Monthly Spend Trend chart |
| 4 | **How much do we spend in foreign currency?** What's our exchange rate exposure? | Risk & Uncertainty dashboard — FX Risk section |

### Supplier Performance
| # | Question | Where to Find the Answer |
|---|----------|--------------------------|
| 5 | **Which suppliers deliver on time?** Who can we trust with urgent orders? | Supplier Performance — OTD vs Quality scatter plot |
| 6 | **Which suppliers have quality problems?** Who causes defects or contamination? | Supplier Performance — Quality Incidents column |
| 7 | **What grade does each supplier get?** (A = excellent, E = unacceptable) | Supplier Performance — Supplier Scorecard |
| 8 | **Are we using unapproved or high-risk suppliers?** | Risk & Uncertainty — Maverick Spend section |

### Savings & Optimization
| # | Question | Where to Find the Answer |
|---|----------|--------------------------|
| 9 | **How much are we overpaying for materials?** (price standardization gap) | Savings Opportunities — Price Variance Opportunities chart |
| 10 | **How much could we save by consolidating suppliers?** | Analysis report — Supplier Consolidation section |
| 11 | **Which suppliers should we keep, and how much business should each get?** | Savings Opportunities — Optimization Recommendations table |
| 12 | **What's the most we could save? The least?** (confidence interval) | Risk & Uncertainty — Monte Carlo Uncertainty Bounds table |
| 13 | **What happens under conservative vs. aggressive assumptions?** | Executive Overview — Scenario Savings Outlook |

### Risk & Compliance
| # | Question | Where to Find the Answer |
|---|----------|--------------------------|
| 14 | **What is our total risk exposure?** (financial, supplier, FX, quality) | Risk & Uncertainty dashboard — full page |
| 15 | **Are any KPIs trending in the wrong direction?** | FMCG Procurement Hub — Alerts section |
| 16 | **Who approved which supplier recommendation and when?** | FMCG Audit Ledger — Recommendation History |
| 17 | **Can the audit log be tampered with?** | Audit Ledger — Hash-chain integrity verification |

### Forecasting & Intelligence
| # | Question | Where to Find the Answer |
|---|----------|--------------------------|
| 18 | **What will demand look like next quarter?** | Intelligence API — Demand Forecast endpoint and Intelligence Summary forecasts |
| 19 | **Are there any unusual spending patterns?** (anomalies) | Intelligence API — Anomaly Detection endpoint |
| 20 | **What is each supplier's risk score?** (multi-factor analysis) | Intelligence API — Risk Scores endpoint |

---

## 5. Decisions You Can Make With This

This platform doesn't just inform — it enables specific, high-impact procurement decisions:

### Decision 1: Supplier Rationalization
**Situation:** You have 12 suppliers for packaging materials.
**Data:** The platform shows you can maintain supply security with just 4, saving 6% through volume consolidation.
**Decision:** Reduce to 4 suppliers. Issue RFQs. Negotiate new contracts.
**Expected Impact:** ₦X million in annual savings per category.

### Decision 2: Price Renegotiation
**Situation:** You're paying 25% more for Material X at one plant vs. another.
**Data:** The platform shows the best available price, who offers it, and the total overpayment.
**Decision:** Standardize pricing across all locations by renegotiating with the lower-cost supplier.
**Expected Impact:** Close the price variance gap — savings quantified to the naira.

### Decision 3: Supplier Replacement
**Situation:** Supplier Z has on-time delivery of only 60% (target: 85%) and 5 quality incidents last year.
**Data:** The platform ranks alternative suppliers by composite score (cost 45%, delivery 30%, quality 15%, risk 10%).
**Decision:** Phase out Supplier Z over 3 months. Redirect volume to top-ranked alternatives.
**Expected Impact:** Reduced production stoppages, lower quality costs.

### Decision 4: Risk Mitigation
**Situation:** 40% of raw materials come from a single supplier.
**Data:** The constrained optimizer recommends capping at 50% and requiring dual-sourcing for categories above 20% of total spend.
**Decision:** Onboard a second qualified supplier for critical categories.
**Expected Impact:** Supply chain resilience improved; single-point-of-failure risk eliminated.

### Decision 5: Budget Planning
**Situation:** The CFO needs a procurement budget range for next year.
**Data:** Monte Carlo simulation provides P05 (worst case), P50 (most likely), and P95 (best case) savings estimates.
**Decision:** Set the budget based on the P50 (median) scenario, with contingency reserves sized by the P05-P50 gap.
**Expected Impact:** More accurate financial planning; fewer budget surprises.

### Decision 6: Supplier Investment
**Situation:** An A/B test (pilot) shows that switching to a new supplier in one region reduced costs by 8%.
**Data:** The KPI catalog measures net revenue uplift, cost reduction, and payback period (e.g., 47 days).
**Decision:** Roll out the supplier switch nationally.
**Expected Impact:** 8% cost reduction scaled across all regions.

### Decision 7: Compliance Action
**Situation:** 13% of spend goes to unapproved (maverick) suppliers.
**Data:** The platform lists every maverick purchase order, the buyer, the amount, and the risk level.
**Decision:** Enforce approved-supplier-list compliance. Implement approval gates in the ERP.
**Expected Impact:** Reduced fraud risk, better negotiated pricing, policy compliance.

---

## 6. How Everything Works — A Plain-English Walkthrough

Let's follow a purchase order from data entry to executive insight:

### Step 1: A Purchase Order Is Created

A buyer in Lagos places an order for 500 kilograms of palm oil from Supplier A at ₦950/kg. This creates a record:

| Field | Value |
|-------|-------|
| PO Number | PO-2024-001 |
| Date | 2024-03-15 |
| Supplier | Ogun Agro Industries |
| Material | Crude Palm Oil |
| Category | Raw Materials |
| Quantity | 500 KG |
| Unit Price | ₦950 |
| Total | ₦475,000 |
| Expected Delivery | 2024-03-29 |

### Step 2: The Data Is Uploaded and Cleaned

The buyer uploads a CSV file containing this and hundreds of other purchase orders. The platform:

1. **Recognizes the column names** — even if the file says "vendor" instead of "supplier," the system maps it automatically. It knows 50+ common aliases for each field.
2. **Validates every row** — checks that quantities are positive, dates make sense, prices are reasonable, and the math adds up (500 × ₦950 = ₦475,000 ✓).
3. **Fills in gaps** — if the file is missing a "delivery_status" column, the platform adds it with a default value.
4. **Reports data quality** — "Your upload has 2,487 valid rows, 13 rows with issues (3 negative quantities, 10 missing delivery dates)."

### Step 3: The Data Goes Into the Analytical Store

The cleaned data is loaded into a structured database (SQLite) with pre-built analytical views:

- **Supplier Performance View** — aggregates each supplier's total orders, total spend, on-time delivery rate, quality incident count, and quality cost.
- **Category Spend View** — groups spending by category, year, and month.
- **Savings Opportunity View** — compares each supplier's price for each material against the lowest available price.

These views are like pre-calculated summary tables that make the analysis run instantly instead of recalculating from scratch every time.

### Step 4: The Analysis Engine Runs

Now the platform runs its analysis pipeline — a sequence of calculations that build on each other:

#### 4a. Executive Summary
"Your total spend is ₦310.39 billion across 2,500 purchase orders from 40 suppliers."

#### 4b. Pareto Analysis (80/20 Rule)
"Raw Materials account for 45% of spend. Packaging is 28%. Together, just 2 of your 4 categories represent 73% of all money spent." This tells you where to focus your negotiation energy.

#### 4c. Price Standardization Analysis
For each material, it finds every price paid and calculates the gap: "Crude Palm Oil — lowest price ₦850/kg, highest ₦1,100/kg, variance 29%. If everyone paid the lowest price, you'd save ₦18.45 billion."

#### 4d. Supplier Performance Scoring
Each supplier gets a composite score:
- **Unit Cost (45% weight):** Lower cost = better score
- **Delivery (30% weight):** Higher on-time percentage = better score
- **Quality (15% weight):** Fewer quality incidents = better score
- **Risk (10% weight):** Lower risk level = better score

Suppliers are then graded A through E:
- **A** = On-time delivery ≥95%, zero quality incidents
- **E** = On-time delivery <70% or 5+ quality incidents

#### 4e. Maverick Spend Detection
"₦40.61 billion (13.08% of total spend) went to non-approved or high-risk suppliers. Top offenders: [Buyer Name] placed 23 orders worth ₦2.1 billion with unapproved vendors."

#### 4f. FX Risk Assessment
"Total USD-denominated spend: $132.41 million. NGN/USD exchange rate volatility over the period: 99.84%. At-risk amount at 1 standard deviation: ₦X billion."

### Step 5: The Optimization Engine Runs

Now the math gets serious. The platform uses **Mixed-Integer Linear Programming (MILP)** — the same category of mathematics used by airlines to schedule flights and by logistics companies to plan delivery routes.

**What it does:** For each purchasing category (e.g., Raw Materials), the solver:

1. Lists all possible suppliers and their scores
2. Decides which suppliers to keep (a binary yes/no decision for each)
3. Decides what percentage of spending to allocate to each selected supplier
4. Minimizes total weighted cost across all selected suppliers
5. Subject to constraints:
   - Must allocate 100% of demand (no demand goes unfulfilled)
   - Maximum 3 suppliers per category (consolidation)
   - Each selected supplier gets at least 15% (no token amounts)
   - No single supplier exceeds 80% (no over-concentration)

**Then, the Constrained Optimizer adds real-world rules:**
- Only suppliers with ≥85% on-time delivery qualify
- Exclude high-risk suppliers
- Categories above 20% of total spend must have at least 2 suppliers (dual-sourcing)

**Output:** A specific recommendation table:

| Category | Supplier | Recommended Share | Projected Spend |
|----------|----------|-------------------|-----------------|
| Raw Materials | Ogun Agro | 50% | ₦X billion |
| Raw Materials | Delta Foods | 35% | ₦Y billion |
| Raw Materials | Abuja Supply | 15% | ₦Z billion |

### Step 6: Scenario Analysis & Monte Carlo

The system then stress-tests those recommendations:

**Scenario Analysis** applies multipliers:
- **Conservative:** Only 50% of price savings will be realized, 60% of performance improvements, 40% of consolidation benefits
- **Base case:** 100% realization (our best estimate)
- **Aggressive:** 150% of price savings (maybe we negotiate even harder)

This gives three savings numbers: conservative ₦X, base ₦Y, aggressive ₦Z.

**Monte Carlo Simulation** goes further. It runs 10,000 random scenarios where:
- Price savings vary randomly ±15% from the base estimate
- Performance improvement varies ±20%
- Consolidation savings vary ±25%
- Total spend itself varies ±5%

From 10,000 results, you get a probability distribution:
- **5th percentile (P05):** "Even in a bad scenario, we save at least ₦150 billion"
- **50th percentile (P50/Median):** "Most likely savings are ₦186 billion"
- **95th percentile (P95):** "In an optimistic scenario, we could save ₦225 billion"

This answers the CFO's question: "How confident should I be in these numbers?"

### Step 7: Results Are Presented

All of this information — the summaries, the charts, the recommendations, the risk analysis — is delivered through:

1. **An interactive web dashboard** (8 pages)
2. **A Power BI export pack** (for Microsoft-based reporting)
3. **A REST API** (for integration with other systems)
4. **Machine-readable JSON** (for data pipelines)

### Step 8: Humans Decide and Act

The platform doesn't auto-implement anything (that would be dangerous). Instead:

1. A recommendation is logged in the **event ledger** (e.g., "Switch 30% of Raw Materials spend from Supplier X to Supplier Y")
2. An **approver** reviews the recommendation, sees the supporting data, and either **approves** or **rejects** it
3. Every action is permanently recorded with a timestamp, the person's ID, and a hash that chains to the previous entry (tamper-evident and integrity-verifiable)
4. Alerts fire if any KPI drifts beyond acceptable thresholds — for example, if a recommended supplier starts underperforming

---

## 7. Step-by-Step Project Walkthrough

This section describes, in chronological order, every step taken to build the Aegis Procurement Intelligence Platform from concept to completion.

### Phase 0: Problem Definition & Data Understanding

**Goal:** Understand what procurement analytics problems exist and how they're currently being solved (or not solved).

1. **Analyzed a real FMCG dataset** to understand the structure of procurement/sales data: purchase orders, supplier records, material catalogs, quality incidents
2. **Identified 6 core problems:** price variance, supplier performance gaps, over-fragmented supply base, maverick spending, unquantified uncertainty, and lack of audit trails
3. **Defined the target user:** Chief Procurement Officer (CPO), procurement managers, category managers, finance teams, and supply chain analysts

### Phase 1: Data Layer — Generation, Validation, and Storage

**Goal:** Build a solid data foundation that accepts messy real-world data and transforms it into a clean, analyzable format.

4. **Built a synthetic data generator** (`generate_data.py`): Creates 2,500 purchase orders across 40 suppliers and 71 materials, with realistic pricing variance, delivery delays, and quality incidents. Uses Nigerian Naira (NGN) as the primary currency with USD cross-currency exposure.

5. **Created a database loader** (`create_db.py`): Loads CSV files into SQLite, creates performance indexes, and builds 3 pre-computed analytical views (supplier performance, category spend, savings opportunities).

6. **Built a column-alias normalizer** (`dashboard_data.py`): Recognizes 50+ column name variations so data from SAP, Oracle, Coupa, or manual spreadsheets all map to the same canonical schema. Handles "vendor_id" → "supplier_id", "order_date" → "po_date", "payment_term" → "payment_terms", etc.

7. **Created validation schemas** (`validation/schemas.py`): 4 Pandera schemas (Suppliers, Materials, Purchase Orders, Quality Incidents) that enforce data types, ranges, uniqueness, and cross-field consistency (e.g., total = quantity × price).

8. **Added security-layer input validation** (`security.py`): Sanitizes filenames (blocks path traversal attacks), validates text payloads (blocks null bytes), enforces file size limits.

### Phase 2: Analytics Engine — Metrics, KPIs, and Reconciliation

**Goal:** Define standardized business metrics and ensure the math is always correct.

9. **Built a Semantic Metrics Layer** (`fmcg/metrics.py`): 7 registered formulas — gross sales, net sales, promo ROI, gross-to-net leakage, unit margin, purchase cost total, contribution margin. Metrics are defined once, computed consistently everywhere.

10. **Created a Reconciliation Suite** (`fmcg/reconciliation.py`): 7 cross-check rules that validate financial correctness row by row. "Does gross_sales = units × price?" "Is discount between 0% and 100%?" Any violation is flagged by row index.

11. **Defined a KPI Catalog** (`fmcg/kpi_catalog.py`): 8 standardized KPIs across commercial, procurement, and shared categories. Each has a human-readable formula string, a callable computation function, a designated owner (Commercial vs. Procurement), and a recommended reporting cadence (weekly/monthly).

12. **Built a Feature Store** (`fmcg/features.py`): 8 demand-driver features that transform raw data into categorical signals: is it a promo day? What's the discount depth? Is stock at risk? What price tier is this SKU in? These features feed the machine learning models.

### Phase 3: Optimization & Simulation

**Goal:** Move beyond descriptive analytics ("what happened") to prescriptive analytics ("what should we do").

13. **Built a Supplier Optimization Engine** (`optimization_engine.py`): Scores every supplier on a weighted composite (cost 45%, delivery 30%, quality 15%, risk 10%), then uses mathematical programming to find the optimal supplier mix per category. Respects minimum/maximum supplier count and allocation share constraints.

14. **Added Constrained Optimization** (`constrained_optimization.py`): Layer on top of the optimizer that enforces business policies — OTD floors, quality thresholds, risk limits, dual-sourcing rules. Makes recommendations implementable.

15. **Implemented the MILP Solver** (`optimization/mathematical.py`): The actual mathematics — a Mixed-Integer Linear Program using `scipy.optimize.milp`. Models the problem as: minimize weighted supplier cost subject to allocation and selection constraints. Returns exact allocation percentages.

16. **Built Scenario Analysis** (`scenario_analysis.py`): Apply conservative/base/aggressive multipliers to each savings component. Produces a 3-row comparison table that shows best, expected, and worst-case savings.

17. **Built Monte Carlo Simulation** (`monte_carlo.py`): 10,000 random draws from normal distributions centered on base savings estimates, each with calibrated uncertainty (±15% for price, ±20% for performance, ±25% for consolidation). Produces P05/P25/P50/P75/P95 confidence intervals.

### Phase 4: Machine Learning & Intelligence

**Goal:** Add AI capability that goes beyond rule-based analysis.

18. **Demand Forecasting** (`ml/models.py`): A Random Forest model trained on historical purchase order volumes with calendar features (month number, quarter). Predicts future category demand 3 months ahead. Falls back to mean forecasting if insufficient data.

19. **Anomaly Detection** (`ml/models.py`): An Isolation Forest algorithm that identifies unusual spending patterns — purchase orders that differ significantly from the norm in quantity, price, or amount. Returns an anomaly score for every transaction.

20. **AI Intelligence Suite** (`intelligence.py`): Five advanced engines:
    - **Spend Anomaly Detector** — ensemble of Z-score, IQR, and Isolation Forest methods
    - **Demand Forecast Engine** — Gradient Boosting with exponential smoothing fallback
    - **Supplier Risk Engine** — 6-dimension weighted scoring with letter grades
    - **Insight Generator** — templates that produce plain-English explanations from numbers
    - **Savings Opportunity Finder** — identifies consolidation, price-variance, and timing-based savings

### Phase 5: Dashboard & Visualization

**Goal:** Make the analytics accessible to non-technical users through interactive dashboards.

21. **Built the main Streamlit application** (`streamlit_app.py`): Landing page with KPI strip, spend-by-category chart, monthly trend, and navigation to 8 detail pages.

22. **Page 01 — Executive Overview**: Spend distribution, KPI summary table, monthly trends, and scenario savings outlook. Designed for CPOs and CFOs.

23. **Page 02 — Supplier Performance**: Supplier scorecard, OTD vs. Quality Cost scatter plot, performance grade distribution, top 15 suppliers by spend. Designed for category managers.

24. **Page 03 — Savings Opportunities**: Price variance opportunities, optimization recommendations, constrained sourcing plan, scenario comparison. Designed for procurement strategists.

25. **Page 04 — Risk & Uncertainty**: Maverick spend breakdown, FX risk exposure, Monte Carlo uncertainty bounds. Designed for risk officers.

26. **Page 05 — Data Hub**: Data quality report, column mappings, schema reference, Power BI export, raw data preview. Designed for analysts and data teams.

27. **Page 06 — FMCG Commercial Command Centre**: Net-sales trends, category revenue mix, discount depth analysis, gross-to-net leakage. Designed for commercial/sales teams.

28. **Page 07 — FMCG Procurement Hub**: Active procurement alerts, recommendation workflow, lead-time tracking, negotiation realization. Designed for procurement operations.

29. **Page 08 — FMCG Audit & Recommendation Ledger**: Recommendation volume, approval latency, decision mix, full searchable history, JSONL export. Designed for compliance and internal audit.

### Phase 6: API Layer & Access Control

**Goal:** Make data accessible programmatically and enforce permissions.

30. **Built the FMCG API Router** (`fmcg/api_router.py`): 15 REST endpoints for schema validation, metric computation, KPI evaluation, pilot selection, alert evaluation, event logging, compaction, archiving, and approval workflow.

31. **Created RBAC System** (`fmcg/access_control.py`): 4 roles (Viewer, Analyst, Approver, Admin) with 13 granular permissions. Every API endpoint checks the caller's permission before executing.

32. **Built the Event Ledger** (`fmcg/event_log.py`): Append-only JSONL (JSON Lines) file that records every recommendation and every decision as an immutable event. Supports ledger compaction and archiving to a secondary file.

33. **Built Variance Alerts** (`fmcg/variance_alerts.py`): 4 rules that fire when current-period metrics deviate from baseline beyond threshold: gross-to-net leakage >15%, net sales drop >10%, purchase cost increase >5%, lead time worsening >20%.

### Phase 7: SaaS Platform Transformation

**Goal:** Transform the analytics tool into a multi-tenant commercial platform.

34. **Multi-Tenant Foundation** (`tenant.py`): 4 pricing tiers (Free, Starter, Professional, Enterprise), 3 isolation modes, per-tenant context propagation using Python context variables (thread-safe), tenant CRUD via a Registry.

35. **Authentication System** (`auth.py`): JWT token issuance (HMAC-SHA256, 1-hour access + 30-day refresh), API key management (SHA-256 hashed storage, revocable, scoped), token-bucket rate limiting per tenant.

36. **Real-Time Streaming** (`streaming.py`): In-process event bus (pub/sub), Server-Sent Events (SSE) channels per tenant, webhook delivery with HMAC signing and circuit breaker pattern (auto-disable after 10 consecutive failures).

37. **Billing & Subscriptions** (`billing.py`): 4 plan tiers with defined limits (5 to unlimited users, 10K to unlimited API calls per month, 100K to unlimited upload rows), usage metering for 6 metrics, invoice generation, Stripe integration points.

38. **SaaS API Router** (`api/saas_router.py`): 20+ REST endpoints under `/v1/` — tenant management, token issuance, API key lifecycle, intelligence queries, SSE streaming, webhook management, plan listing, subscription management, usage reporting, invoice history.

39. **Python SDK** (`sdk.py`): Zero-dependency client library (uses only Python standard library) with automatic retry, exponential backoff, SSE streaming, and typed resource namespaces (tenants, auth, intelligence, events, webhooks, billing).

### Phase 8: Security, Compliance & Audit

**Goal:** Meet enterprise security and regulatory requirements.

40. **Compliance Module** (`compliance.py`):
    - **PII Masking** — automatically detects and redacts email addresses, phone numbers, and credit card numbers in any text
    - **Data Classification** — auto-classifies fields into 4 sensitivity levels (Public, Internal, Confidential, Restricted) based on naming conventions
    - **Hash-Chain Audit Log** — every audit entry is linked to the previous one via SHA-256 hash, creating a tamper-evident chain (like a simplified blockchain)
    - **GDPR Service** — handles Data Subject Access Requests (DSARs): access, erasure, portability, and rectification workflows
    - **Encryption Service** — AES-256-GCM application-layer encryption with PBKDF2-derived per-context keys
    - **SOC 2 Compliance Checker** — automated assessment of 14 controls (CC1–CC9) with evidence collection and compliance scoring

### Phase 9: Infrastructure & Deployment

**Goal:** Define production-grade cloud infrastructure.

41. **AWS Infrastructure** (`infrastructure/aws/main.tf`): Full Terraform configuration for:
    - VPC with 3 availability zones (3 public, 3 private subnets, NAT gateway)
    - ECS Fargate (serverless containers, auto-scaling 3–20 instances)
    - Aurora PostgreSQL Serverless v2 (auto-scales from 0.5 to 16 compute units)
    - ElastiCache Redis (caching and rate limiting)
    - S3 Data Lake (versioned, KMS-encrypted, lifecycle tiering)
    - SQS queues for ML jobs and webhook delivery (with dead-letter queues)
    - KMS encryption for data at rest, Secrets Manager for credentials

42. **Web Application Firewall** (`infrastructure/aws/waf.tf`): WAF v2 with OWASP rules, SQL injection protection, rate limiting (2,000 requests per 5 minutes per IP), and known-bad-input blocking.

43. **Vercel Frontend** (`infrastructure/vercel/vercel.json`): Multi-region deployment (US East, US West, Europe), security headers (HSTS, Content Security Policy, X-Frame-Options), API route rewriting, and scheduled cron jobs.

44. **Production Docker Image** (`Dockerfile.production`): Multi-stage build for minimal attack surface — builder stage compiles dependencies, runtime stage uses non-root user, health check endpoint.

45. **CI/CD Pipeline** (`.github/workflows/ci.yml`): 5-stage GitHub Actions workflow — lint (Ruff) → test (≥80% code coverage required) → security scan (Bandit + Safety + Trivy) → Docker build with vulnerability scanning → deploy to ECS with rollback-on-failure.

### Phase 10: Power BI Integration

**Goal:** Bridge to the Microsoft BI ecosystem.

46. **DAX Measures** (`powerbi/DAX_MEASURES.md`): Pre-built DAX formulas for Power BI: Total Spend, Order Count, Category %, YoY Growth, Savings %, and 10+ other commonly needed measures.

47. **Field Mappings** (`powerbi/powerbi_field_mapping.csv`): CSV that maps every database column to its Power BI display name, data type, and formatting.

48. **Theme & Spec** (`powerbi/powerbi_theme.json`, `POWERBI_PBIT_STARTER_SPEC.json`): Visual configuration — corporate color scheme, font settings, chart defaults.

49. **Deployment Guide** (`powerbi/POWERBI_DEPLOYMENT_GUIDE.md`): Step-by-step instructions for connecting Power BI Desktop to the exported data pack.

### Phase 11: Observability & Monitoring

**Goal:** Know what the system is doing at all times.

50. **Structured JSON Logging** (`observability/logging.py`): Every log entry is a JSON object with timestamp, level, logger name, message, and optional fields (request_id, path, duration_ms, status_code). Designed for ingestion by Elasticsearch, CloudWatch, or Datadog.

51. **Prometheus Metrics** (`observability/metrics.py`): Two core metrics — request count (by method, path, status code) and request latency histogram (by method, path). Exposed via `/metrics` endpoint for Prometheus/Grafana scraping.

### Phase 12: Testing & Quality

**Goal:** Verify everything works and keep it working.

52. **194 automated tests across 14+ test files**, covering:
    - Data validation and schema enforcement
    - Financial reconciliation rules
    - Optimization engine outputs
    - Monte Carlo simulation bounds
    - API endpoint behavior
    - RBAC permission enforcement
    - Event log integrity and workflow
    - Tenant isolation and context propagation
    - JWT encoding/decoding and API key lifecycle
    - Rate limiting and usage metering
    - Billing plan logic and subscription management
    - Real-time streaming and webhook signing
    - Compliance: PII masking, audit log hash-chain integrity, GDPR DSAR workflow, encryption roundtrip
    - Input security (path traversal blocking, null byte detection)

---

## 8. The Technology Behind It

### Languages & Frameworks

| Technology | What It Does | Why We Use It |
|-----------|-------------|---------------|
| **Python 3.13** | Primary programming language | Industry standard for data analytics and ML |
| **FastAPI** | REST API framework | Auto-generates documentation, async-capable, very fast |
| **Streamlit** | Dashboard framework | Turns Python scripts into web apps without frontend code |
| **Pydantic v2** | Data validation | Enforces data types and constraints; catches errors early |
| **Pandera** | DataFrame validation | Schema enforcement specifically for tabular data |
| **scikit-learn** | Machine learning | Isolation Forest (anomaly detection), Random Forest (forecasting) |
| **SciPy** | Mathematical optimization | MILP solver for supplier allocation |
| **NumPy** | Numerical computing | Monte Carlo simulation, statistical calculations |
| **pandas** | Data manipulation | The standard library for tabular data operations |
| **Plotly** | Charting | Interactive charts that work in web browsers |
| **SQLite** | Embedded database | Zero-configuration database for analytical queries |

### Architecture Patterns

| Pattern | What It Means | Where It's Used |
|---------|--------------|----------------|
| **Append-only ledger** | Data is never modified, only added to | Event log (audit trail) |
| **Hash chain** | Each record links to the previous via cryptographic hash | Tamper-proof audit log |
| **Context variables** | Thread-safe per-request state | Tenant isolation in multi-tenant SaaS |
| **Token bucket** | Rate limiting algorithm | API rate limiting per tenant |
| **Pub/sub event bus** | Publishers emit events; subscribers react | Real-time streaming and webhooks |
| **MILP** (Mixed-Integer Linear Programming) | Mathematical optimization with integer constraints | Supplier allocation |
| **Monte Carlo simulation** | Random sampling to model uncertainty | Savings confidence intervals |
| **Feature store** | Registry of named, versioned data transformations | Demand-driver feature engineering |
| **Semantic metrics layer** | Centralized metric definitions | Business metrics (revenue, margin, etc.) |
| **RBAC** (Role-Based Access Control) | Users get roles; roles have permissions | API endpoint authorization |

### Infrastructure & Deployment

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Compute** | AWS ECS Fargate | Serverless container hosting (no server management) |
| **Database** | Aurora PostgreSQL Serverless v2 | Auto-scaling relational database |
| **Cache** | ElastiCache Redis | In-memory cache for rate limiting and session data |
| **Storage** | S3 + KMS | Encrypted data lake with lifecycle tiering |
| **CDN / Frontend** | Vercel | Global edge deployment for static assets |
| **CI/CD** | GitHub Actions | 5-stage build-test-scan-deploy pipeline |
| **Firewall** | AWS WAF v2 | OWASP protection, SQL injection, rate limiting |
| **Monitoring** | Prometheus + CloudWatch | Metrics scraping and centralized logging |
| **Containers** | Docker (multi-stage) | Minimal, secure production images |
| **Infrastructure-as-Code** | Terraform | Repeatable, version-controlled infrastructure |

---

## 9. Dashboard Pages — What Each Screen Shows

### Page 1: Executive Overview 📊
**Who it's for:** CPO, CFO, C-suite executives
**What it shows:**
- Total spend broken down by category (bar chart with percentages)
- Key metrics at a glance: total spend, total orders, average order value, total savings potential
- Monthly spending trend over time (line chart — are we spending more or less?)
- Scenario savings outlook: conservative, base, and aggressive projections
**Key insight:** "We spend ₦310 billion annually. 60% of that has identified optimization potential."

### Page 2: Supplier Performance 🏭
**Who it's for:** Category managers, procurement leads
**What it shows:**
- Ranked supplier scorecard (graded A through E)
- Scatter plot: on-time delivery vs. quality cost (find suppliers that are both late AND costly)
- Distribution of grades across categories
- Top 15 suppliers by total spend
**Key insight:** "Supplier X is grade D — 68% on-time delivery and ₦4.2 billion in quality costs. Consider replacement."

### Page 3: Savings Opportunities 💰
**Who it's for:** Strategic sourcing team
**What it shows:**
- Price variance opportunities ranked by potential savings (bar chart)
- Mathematical optimization results: recommended supplier mix per category
- Constrained sourcing plan with business rules applied
- Side-by-side scenario comparison
**Key insight:** "Consolidating from 12 to 4 packaging suppliers and standardizing pricing saves ₦18.45 billion."

### Page 4: Risk & Uncertainty ⚠️
**Who it's for:** Risk officers, finance team
**What it shows:**
- Maverick spend breakdown by risk level
- Foreign exchange exposure (USD denominated spend, volatility range)
- Monte Carlo uncertainty bounds (5th to 95th percentile savings)
**Key insight:** "Even in our worst-case scenario (P05), we still save ₦150 billion. The downside risk is manageable."

### Page 5: Data Hub 📂
**Who it's for:** Data analysts, IT team
**What it shows:**
- Data quality report (completeness, validity)
- Detected column mappings (what renaming the system did)
- Upload schema reference (what columns are expected)
- Power BI export pack download
- Raw data preview
**Key insight:** "Your upload is 98.7% clean. 13 rows have issues — here are the specifics."

### Page 6: FMCG Commercial Command Centre 💹
**Who it's for:** Commercial/sales teams
**What it shows:**
- Net sales trend by category (daily time series)
- Revenue mix (donut chart)
- Discount depth analysis and gross-to-net leakage
- Promo ROI
**Key insight:** "Category Y has 22% gross-to-net leakage — we're discounting too aggressively."

### Page 7: FMCG Procurement Hub 🔗
**Who it's for:** Procurement operations
**What it shows:**
- Active variance alerts (color-coded by severity)
- Recommendation workflow (pending, approved, rejected)
- Lead-time monitoring
- Negotiated savings realization tracker
**Key insight:** "Supplier Z's lead time has worsened by 25% — this triggered a WARNING alert."

### Page 8: FMCG Audit & Recommendation Ledger 🧾
**Who it's for:** Internal audit, compliance
**What it shows:**
- Recommendation volume over time
- Decision breakdown (how many approved vs. rejected vs. pending)
- Approval latency distribution (how long decisions take)
- Recent hash-chain link inspector with recorded vs. expected hashes
- Complete searchable history
- JSONL export for external audit tools
**Key insight:** "47 recommendations logged this quarter. Average approval time: 3.2 days. 0 integrity violations detected."

---

## 10. The SaaS Platform Layer

The platform is designed to serve multiple companies simultaneously as a Software-as-a-Service product.

### Multi-Tenancy: How Company Data Stays Separate

When Company A uploads their data, it must never be visible to Company B. The platform achieves this through:

1. **Tenant Context Variables** — every API request carries a tenant ID, which is propagated through every layer of the code using Python's `contextvars` (like a nametag that travels with the request)
2. **Tenant Registry** — a central registry that knows every tenant, their tier, their limits, and whether they're active
3. **Isolation Modes** — Free/Starter tiers share infrastructure (SHARED mode); Enterprise gets dedicated resources (DEDICATED mode)

### Authentication: How We Know Who You Are

Three methods, each for different use cases:

| Method | Best For | How It Works |
|--------|---------|-------------|
| **JWT Token** | Human users (dashboard login) | User logs in; gets a token valid for 1 hour; token contains user ID, tenant ID, roles |
| **API Key** | Server-to-server integration | Company generates a key (starts with `pi_live_`); includes it in every API call; key is hashed with SHA-256 for storage |
| **Refresh Token** | Extending sessions | A 30-day token that can be exchanged for a new 1-hour access token |

### Rate Limiting: Preventing Overuse

Each tenant tier has API call limits (e.g., Free = 10,000/month, Starter = 100,000/month). The system uses a **token bucket** algorithm — imagine a bucket that refills at a steady rate. Each API call removes a token. If the bucket is empty, the request is rejected with a "429 Too Many Requests" response.

### Pricing Tiers

| Tier | Price | Users | API Calls/Month | Upload Rows | Storage | Key Features |
|------|-------|-------|-----------------|-------------|---------|-------|
| **Free** | ₦0 | 5 | 10,000 | 100,000 | 1 GB | Core analytics, community support |
| **Starter** | ₦99/mo | 25 | 100,000 | 1,000,000 | 10 GB | + Real-time streaming, email support |
| **Professional** | ₦499/mo | 100 | 1,000,000 | 10,000,000 | 100 GB | + SSO/SAML, SLA, priority support |
| **Enterprise** | Custom | Unlimited | Unlimited | Unlimited | 10 TB | + Dedicated infra, SOC 2, data residency |

### Real-Time Events

When something happens (an anomaly is detected, a recommendation is created, an upload completes), the platform can notify you in real time through:

- **Server-Sent Events (SSE)** — a persistent HTTP connection that streams updates to your browser
- **Webhooks** — the platform sends an HTTP POST to your server when an event occurs, signed with HMAC-SHA256 so you can verify it's authentic

---

## 11. Infrastructure & Deployment

### Cloud Architecture (AWS)

```
         ┌─────────────────────────────────────┐
         │           AWS Cloud (VPC)            │
         │                                       │
         │   ┌─────────┐        ┌────────────┐  │
Internet─┼──►│ WAF + ALB│───────►│ ECS Fargate │  │
         │   │ (HTTPS)  │        │ (3-20 tasks)│  │
         │   └─────────┘        └──────┬──────┘  │
         │                              │         │
         │              ┌───────────────┼──────┐  │
         │              │               │      │  │
         │        ┌─────▼────┐   ┌──────▼───┐  │  │
         │        │  Aurora   │   │  Redis   │  │  │
         │        │ PostgreSQL│   │ (Cache)  │  │  │
         │        │ Serverless│   └──────────┘  │  │
         │        └──────────┘                  │  │
         │                                       │  │
         │   ┌──────────┐    ┌───────────────┐  │  │
         │   │ S3 Data  │    │   SQS Queues  │  │  │
         │   │ Lake     │    │ (ML + Webhooks)│  │  │
         │   └──────────┘    └───────────────┘  │  │
         └─────────────────────────────────────┘
```

- **WAF (Web Application Firewall):** Blocks SQL injection, cross-site scripting, and brute-force attacks before they reach the application
- **ALB (Application Load Balancer):** Distributes traffic across multiple application containers; terminates HTTPS/TLS 1.3
- **ECS Fargate:** Runs the application in Docker containers without managing servers; auto-scales from 3 to 20 instances based on CPU utilization (target: 70%)
- **Aurora PostgreSQL Serverless v2:** Database that automatically scales from 0.5 to 16 compute units based on load; encrypted at rest with KMS
- **Redis:** In-memory cache for rate limiting, session state, and frequently accessed data
- **S3:** Long-term data storage (data lake) with versioning and automatic lifecycle tiering: active → Intelligent Tiering (90 days) → Glacier archive (365 days)
- **SQS:** Message queues for background work — ML job processing and webhook delivery, each with a dead-letter queue for failed messages
- **KMS:** Encryption key management — all data encrypted at rest

### CI/CD Pipeline

Every code change goes through a 5-stage automated pipeline:

```
  Push Code     →    Lint     →     Test      →    Security    →    Build     →    Deploy
  (GitHub)           (Ruff)        (Pytest)        (Bandit +        (Docker +      (ECS +
                     Check         ≥80% cov        Safety +         Trivy         Smoke
                     formatting)                    Trivy)           scan)         test)
```

1. **Lint:** Code style and formatting checks (catches basic errors instantly)
2. **Test:** Run 190+ tests with ≥80% code coverage requirement
3. **Security:** Static analysis for Python vulnerabilities (Bandit), dependency vulnerability scan (Safety), container image scan (Trivy)
4. **Build:** Build the Docker image and push to AWS ECR (container registry)
5. **Deploy:** Update the ECS service, wait for it to stabilize, run a smoke test against the health endpoint; if anything fails, automatically roll back

---

## 12. Security, Compliance & Audit

### Data Protection

| Layer | Protection | How It Works |
|-------|-----------|-------------|
| **In Transit** | TLS 1.3 | All data encrypted between browser and server |
| **At Rest** | AES-256 via KMS | All database and S3 data encrypted with AWS managed keys |
| **Application** | AES-256-GCM | Sensitive application payloads encrypted with PBKDF2-derived per-context keys |
| **PII** | Automatic Masking | Email, phone, credit card patterns detected and redacted |

### Audit Trail

Every action in the system is permanently recorded in an append-only audit log:

```
Entry #1: { action: "LOGIN", actor: "user_42", timestamp: "2024-03-15T09:00:00Z", hash: "a1b2c3..." }
Entry #2: { action: "DATA_UPLOAD", actor: "user_42", timestamp: "2024-03-15T09:01:00Z", prev_hash: "a1b2c3...", hash: "d4e5f6..." }
Entry #3: { action: "RECOMMENDATION_APPROVED", actor: "user_17", timestamp: "2024-03-15T14:30:00Z", prev_hash: "d4e5f6...", hash: "g7h8i9..." }
```

Each entry's hash is computed from its own contents plus the previous entry's hash. If anyone modifies Entry #2 after the fact, Entry #3's hash won't match — and integrity verification will detect the tampering.

### GDPR Compliance

The platform supports Data Subject Access Requests (DSARs):

- **Right to Access:** An individual can request all data held about them
- **Right to Erasure:** An individual can request their data be deleted
- **Right to Portability:** An individual can request their data in a machine-readable format
- **Right to Rectification:** An individual can request corrections to their data

Each DSAR is logged, tracked through a workflow (pending → processing → completed/denied), and recorded in the audit trail.

### SOC 2 Controls

The compliance checker automatically assesses 14 security controls:

| Control | Description |
|---------|-------------|
| CC1.1 | Organization demonstrates commitment to integrity |
| CC2.1 | Information communicated internally about objectives |
| CC3.1 | Risk assessment process established |
| CC4.1 | Monitoring activities established |
| CC5.1 | Control activities selected and developed |
| CC6.1 | Logical access security implemented |
| CC6.2 | Access credentials managed properly |
| CC6.3 | Access to systems controlled |
| CC7.1 | System changes managed |
| CC7.2 | System changes tested |
| CC8.1 | Change management procedures established |
| CC9.1 | Risk mitigation activities implemented |
| CC9.2 | Entity identifies vendor risk |
| ... | Evidence collected automatically from system configuration |

The platform calculates a **compliance score** (0–100%) based on how many controls are satisfied, with evidence collected automatically from the system's configuration and runtime state.

---

## 13. Testing & Quality Assurance

### Test Coverage

| Test Area | File | Tests | What's Verified |
|-----------|------|-------|----------------|
| API Endpoints | test_api_app.py | 10 | Health check, CORS, metrics, FMCG event lifecycle, SaaS intelligence responses |
| Authentication | test_auth.py | 15 | JWT encode/decode, API keys, rate limiting |
| Benchmark | test_benchmark_profile.py | 1 | Performance regression detection |
| Billing | test_billing.py | 19 | Plans, subscriptions, usage, invoices |
| CLI Pipeline | test_cli.py | 1 | End-to-end command-line execution |
| Compliance | test_compliance.py | 26 | PII masking, audit chain, GDPR, encryption, ciphertext tamper detection |
| Optimization | test_constrained_optimization.py | 3 | Constrained solver correctness |
| Dashboard Data | test_dashboard_data.py | 13 | Normalization, analytics, export |
| FMCG Foundation | test_fmcg_foundation.py | 12 | Models, reconciliation, metrics, features |
| FMCG Milestone 2 | test_fmcg_m2.py | 31 | KPIs, pilot, RBAC, event log, alerts, API, ledger tamper detection |
| Data Integrity | test_integrity_regression.py | 2 | End-to-end data pipeline integrity |
| Intelligence | test_intelligence.py | 13 | Anomalies, forecasting, risk, insights |
| Math Optimization | test_mathematical_optimization.py | 1 | MILP solver correctness |
| ML Models | test_ml_models.py | 2 | Forecast output, anomaly output |
| Monte Carlo | test_monte_carlo.py | 7 | Simulation bounds, percentiles, stability |
| Optimization Engine | test_optimization_engine.py | 1 | Supplier optimization output |
| Scenario Analysis | test_scenario_analysis.py | 1 | Sensitivity analysis output |
| SQL Reconciliation | test_sql_metric_reconciliation.py | 3 | SQL metrics match JSON metrics |
| Streaming | test_streaming.py | 16 | Event bus, SSE, webhooks, signing |
| Tenant | test_tenant.py | 14 | Context vars, registry, tiers, isolation |
| Validation & Security | test_validation_security.py | 3 | Schema validation, filename sanitization, payload safety |
| **TOTAL** | **14+ files** | **194** | |

All 194 tests pass. The CI pipeline requires ≥80% code coverage; any test failure blocks deployment.

---

## 14. Key Numbers & Results

### Dataset Scale
| Metric | Value |
|--------|-------|
| Purchase Orders | 2,500 |
| Suppliers | 40 |
| Materials | 71 |
| Categories | 4 (Raw Materials, Packaging, Equipment, Services) |
| Quality Incidents | 150 |
| Time Period | 24 months |
| Total Spend | ₦310.39 billion |

### Savings Identified
| Savings Driver | Amount | % of Spend |
|---------------|--------|------------|
| Price Standardization | ₦18.45 billion | 5.94% |
| Supplier Performance Improvement | ₦167.47 billion | 53.96% |
| Supplier Consolidation | Varies by dataset | ~6% per category |
| **Total Identified** | **₦185.92 billion** | **59.90%** |

### Monte Carlo Confidence Interval (10,000 simulations)
| Percentile | Savings | % of Spend |
|-----------|---------|------------|
| P05 (Worst Case) | ~₦150 billion | ~48% |
| P50 (Median / Most Likely) | ~₦186 billion | ~60% |
| P95 (Best Case) | ~₦225 billion | ~73% |

### Risk Exposure
| Risk Type | Exposure |
|-----------|----------|
| Maverick Spend | ₦40.61 billion (13.08% of total) |
| USD Exposure | $132.41 million |
| FX Volatility | 99.84% range over period |

### Platform Scale
| Metric | Value |
|--------|-------|
| Python Modules | 25+ |
| API Endpoints | 35+ (15 FMCG + 20 SaaS) |
| Dashboard Pages | 8 |
| Automated Tests | 194 |
| Pricing Tiers | 4 |
| ML Algorithms | 5 |
| Compliance Controls | 14 (SOC 2) |
| Terraform Resources | 30+ AWS resources |

---

## 15. Glossary — Terms Explained Simply

| Term | Simple Explanation |
|------|-------------------|
| **API** | A way for computer programs to talk to each other (like a waiter taking orders between you and the kitchen) |
| **Anomaly Detection** | A computer automatically finding things that look "unusual" compared to normal patterns |
| **Append-Only** | You can only add new entries; you can never go back and change old ones |
| **Aurora Serverless** | An Amazon database that automatically grows bigger when busy and shrinks when quiet (you only pay for what you use) |
| **Billing Tier** | Different price levels with different features (like economy vs. business class on a flight) |
| **CI/CD** | Automated pipeline that tests, checks, and deploys code every time a developer makes a change |
| **Context Variable** | A piece of information (like "which company is making this request") that automatically travels through every layer of code |
| **CSV** | A simple spreadsheet format (comma-separated values) that almost any software can read |
| **DAX** | The formula language used in Power BI (Microsoft's data visualization tool) |
| **Docker** | A technology that packages software into a "container" that runs the same way everywhere |
| **Dual-Sourcing** | Having at least 2 suppliers for critical items, so if one fails, you have a backup |
| **ECS Fargate** | Amazon's service for running Docker containers without managing servers |
| **ERP** | Enterprise Resource Planning — large software systems like SAP or Oracle that companies use to manage operations |
| **FX Risk** | The risk that exchange rate changes will make your foreign-currency purchases more expensive |
| **GDPR** | European law requiring companies to protect personal data and give individuals control over their information |
| **Hash Chain** | A sequence where each item includes a fingerprint of the previous item — if anyone changes a middle item, the chain breaks |
| **Isolation Forest** | A machine learning algorithm that detects unusual data points by measuring how "isolated" they are |
| **JWT** | JSON Web Token — a secure, compact way to pass identity information between systems |
| **KMS** | Key Management Service — Amazon's service for managing encryption keys |
| **KPI** | Key Performance Indicator — a specific metric that measures how well something is performing |
| **Maverick Buying** | Purchasing from unapproved suppliers, usually violating company policy |
| **MILP** | Mixed-Integer Linear Programming — a mathematical method for finding the best allocation/combination |
| **Monte Carlo** | A technique that runs thousands of random simulations to understand the range of possible outcomes |
| **Multi-Tenant** | One system serving multiple separate companies, with each company's data isolated from the others |
| **OTD** | On-Time Delivery — the percentage of orders delivered by the promised date |
| **Pandera** | A Python library for validating that tabular data meets specific rules |
| **Pareto** | The "80/20 rule" — often 80% of effects come from 20% of causes (e.g., 80% of spend comes from 20% of suppliers) |
| **PII** | Personally Identifiable Information — data that can identify a person (name, email, phone, etc.) |
| **Power BI** | Microsoft's business intelligence and data visualization tool |
| **RBAC** | Role-Based Access Control — giving users different permissions based on their role (viewer, analyst, admin) |
| **REST API** | A standard web interface where you access data and actions through URLs (like GET /suppliers, POST /recommendations) |
| **SaaS** | Software as a Service — software you access via the internet and pay for with a subscription |
| **SOC 2** | A security certification that proves a company protects customer data properly |
| **SQLite** | A lightweight, file-based database that requires no separate server |
| **SSE** | Server-Sent Events — a way for a server to push real-time updates to a browser |
| **Streamlit** | A Python framework that turns data scripts into interactive web dashboards |
| **Terraform** | A tool that defines cloud infrastructure (servers, databases, networks) as code, so it's repeatable and version-controlled |
| **Token Bucket** | A rate-limiting algorithm — imagine a bucket that refills at a steady rate; each request takes a token out |
| **WAF** | Web Application Firewall — a security layer that blocks common web attacks |
| **Webhook** | An automatic notification sent to your server when an event occurs (like a doorbell that rings when something happens) |

---

*Aegis Procurement Intelligence Platform — Transforming procurement data into strategic advantage.*
