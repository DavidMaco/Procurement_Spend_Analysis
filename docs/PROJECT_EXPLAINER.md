# Procurement Spend Analysis — Plain-English Explainer

> **Who this is for:** Anyone who wants to understand what this project does, why it was built,
> and what real-world value it creates — with zero assumed background in data, finance, or supply
> chain.

---

## Table of Contents

1. [The Problem It Solves](#1-the-problem-it-solves)
2. [The Big Idea — What the Project Does](#2-the-big-idea)
3. [A Walk Through the Data Pipeline](#3-a-walk-through-the-data-pipeline)
4. [The Five Things the Analysis Measures](#4-the-five-things-the-analysis-measures)
5. [How the Savings Numbers Are Calculated](#5-how-the-savings-numbers-are-calculated)
6. [Supplier Scoring and Optimization](#6-supplier-scoring-and-optimization)
7. [Scenarios — Best Case, Worst Case, and In Between](#7-scenarios)
8. [Risk Quantification — Monte Carlo Simulation](#8-risk-quantification--monte-carlo-simulation)
9. [The Live Dashboard — What Each Page Shows](#9-the-live-dashboard)
10. [Decisions That Can Be Made From This](#10-decisions-that-can-be-made-from-this)
11. [Real-World Impact Summary](#11-real-world-impact-summary)

---

## 1. The Problem It Solves

### The business context

Imagine you run a large manufacturing or consumer goods company in Nigeria. Every month, your
purchasing team places hundreds of orders: sugar and flour from local farmers, packaging bottles
from China, industrial machinery from Germany, maintenance contractors from local service firms.

At the end of the year you have **thousands of purchase orders** spread across dozens of suppliers.
You know roughly how much money went out the door. But you do **not** know:

- Are you overpaying for the same item because different teams use different suppliers?
- Which suppliers are consistently delivering late, and how much does that cost you in production
  delays and rush orders?
- How much money is being spent with vendors that were never properly vetted or approved?
- If the Naira weakens against the Dollar this quarter, how much does your import bill grow?
- If you reorganised which suppliers you use, how much cheaper could next year's spend be?

This project answers all of those questions. It turns a pile of transaction records into a
**decision-ready intelligence layer** — telling leadership exactly where money is leaking and
what to do about it.

### The core pain point, in one sentence

> "We have the receipts, but not the insights."

Most procurement teams have excellent record-keeping (every purchase order is logged). What they
lack is the analytical capability to look across all those records simultaneously and surface the
patterns that matter.

---

## 2. The Big Idea

The project works like an **automated financial audit and strategy consultant** for the
procurement function. It:

1. Takes raw transaction data (who bought what, from whom, at what price, when it arrived)
2. Loads it into a structured database so it can be queried efficiently
3. Runs a set of analytical routines that look for specific money-losing patterns
4. Calculates exactly how much money those patterns are costing
5. Proposes a restructured supplier strategy and quantifies the savings
6. Presents everything in an interactive dashboard that any executive can navigate — no
   spreadsheets, no coding required

The output is not just numbers. It is a **ranked action list** with NGN values attached to each
action, so leadership knows which lever to pull first.

---

## 3. A Walk Through the Data Pipeline

Think of the project as a factory assembly line. Raw material goes in one end; a finished
executive report comes out the other.

```
Step 1: Data                Step 2: Database          Step 3: Analysis
┌──────────────┐            ┌─────────────┐            ┌───────────────────┐
│ Suppliers    │            │             │            │ KPI computation   │
│ Materials    │ ──────────>│ procurement │ ──────────>│ Savings modelling │
│ Orders (POs) │  create_db │   .db       │ analyze_   │ Supplier scoring  │
│ Quality logs │            │             │ procurement│ Scenario analysis │
└──────────────┘            └─────────────┘            └───────────────────┘
                                                                │
                                                                ▼
                                               Step 4: Reports & Dashboard
                                               ┌───────────────────────────┐
                                               │ Executive PDF/HTML report │
                                               │ Streamlit live dashboard  │
                                               │ PowerBI-ready exports     │
                                               └───────────────────────────┘
```

### Step 1 — The raw data (four tables)

The project uses four tables that mirror what any real procurement department would have:

| Table | What it contains | Real-world equivalent |
|---|---|---|
| **suppliers** | One row per vendor — their name, country, payment terms, risk rating, whether they're formally approved | Your approved-vendor master list |
| **materials** | One row per product type — category, unit of measure, standard price | Your item catalogue / price list |
| **purchase_orders** | One row per transaction — who bought what, from whom, how many units, at what price, delivery dates | Your ERP or invoice archive |
| **quality_incidents** | One row per quality problem — which PO caused it, the financial cost of the defect | Your quality management system |

For this portfolio project, the data is synthetically generated to mirror a realistic Nigerian FMCG
(Fast-Moving Consumer Goods) company: **2,500 purchase orders, 40 suppliers, 4 spend categories,
over 24 months**.

### Step 2 — Loading into a database (`create_db.py`)

The four CSV files are loaded into a **SQLite database** (`procurement.db`). Think of this as
converting a folder of separate spreadsheets into a single, interconnected filing cabinet where
any question can be looked up instantly.

Crucially, `create_db.py` also creates a **view** called `vw_supplier_performance`. A database
view is like a pre-built summary report that recalculates itself every time you open it. This view
joins the purchase orders and quality incidents tables together and computes, for every supplier:

- How many orders they received
- What percentage were delivered on time
- How many quality incidents occurred
- What the total financial cost of those quality issues was
- A letter-grade (A through D) based on their overall performance

### Step 3 — Analysis (`analyze_procurement.py`)

This is the engine. It runs eight distinct investigations against the database and saves the
results to a JSON file (`procurement_insights.json`) and several CSV reports. The eight
investigations are explained in detail in Section 4 below.

### Step 4 — Reports and Dashboard

The results feed into:
- An **executive PDF/HTML report** — a one-page summary for C-suite readers
- A **live Streamlit dashboard** — an interactive, filterable web app with five pages of charts
  and tables
- **PowerBI-ready CSV exports** — for teams that want to build their own reports in PowerBI

---

## 4. The Five Things the Analysis Measures

### 4.1 Spend Visibility (Pareto Analysis)

**The question:** Where is the money actually going?

**How it works:** All 2,500 purchase orders are grouped by category (Raw Materials, Packaging,
Equipment, Services) and the total spend in each is calculated. Then a **Pareto principle** check
is applied — in most businesses, roughly 80% of the money is spent on 20% of the item types.
Knowing which categories consume the most spend tells leadership where to focus negotiating energy.

**What it reveals:** If Raw Materials consumes 65% of total procurement spend, that category
deserves the most rigorous supplier management. A 5% price reduction there saves far more than
a 15% reduction on a small Services category.

---

### 4.2 Price Standardisation (Overpayment Detection)

**The question:** Are we paying the same price for the same product, or are some teams paying
more than they should?

**How it works:** For every product that is bought from more than one supplier, the analysis
compares the **minimum price paid** against the **average price paid**. The gap — what you're
paying above the cheapest available price — is the potential saving.

The formula used is:

> **Potential saving per item** = (Average price paid − Lowest price paid) ÷ Average price paid × Total spend on that item

Only items with a price difference greater than 10% are flagged, because small variance is
normal. Items with large variance are ranked from highest saving to lowest.

**What it reveals:** If you're buying "Raw Materials Item 3" from five different suppliers and
one sells it for ₦50,000/kg while another charges ₦85,000/kg, and your average is ₦70,000/kg,
you could save 28.6% by directing all orders to the cheaper supplier (or negotiating everyone
down to the best price).

In this dataset: **₦18.45 billion** in price standardisation savings was identified across the
top 10 high-variance materials.

---

### 4.3 Supplier Performance (Who is Failing You)

**The question:** Which suppliers are regularly late or delivering defective goods, and how much
is that costing us?

**How it works:** Two cost components are calculated:

1. **Quality cost** — directly measured from the quality incidents log. Each incident has a
   `cost_impact_ngn` field representing defect remediation, returns, or write-offs.
2. **Late delivery cost** — estimated at **3% of the spend** with underperforming suppliers.
   This 3% represents the cost of expediting rush orders, production line downtime, and
   extra logistics when a key material arrives late.

A supplier is flagged as underperforming if:
- Their on-time delivery rate is below 80%, **or**
- They have more than 2 quality incidents with your company

**What it reveals:** Poor suppliers generate hidden costs that never show up on the invoice.
A supplier charging 10% cheaper per unit can be significantly more expensive once late delivery
and defect costs are included.

In this dataset: **₦167.47 billion** in performance improvement savings was identified — the
single largest savings category — driven by the exceptionally high late-delivery rate of 58.5%.

---

### 4.4 Maverick Buying (Compliance Risk)

**The question:** How much of our money is going to vendors we never approved — or that we know
are high-risk?

**What "maverick buying" means:** When an employee bypasses the official approved supplier list
and orders from whoever is convenient or cheapest in the moment, that is called maverick buying.
It creates financial, legal, and supply chain risk because unapproved vendors haven't been vetted
for quality, financial stability, regulatory compliance, or ethical practices.

**How it works:** Every purchase order is cross-referenced against the suppliers table. Orders
placed with suppliers where `is_approved = False` or `risk_level = 'High'` are flagged as
maverick spend. The total is calculated as a currency amount and a percentage of total spend.

**What it reveals:** If 13% of spend is maverick, that means 13 cents of every Naira you spend
on procurement carries unchecked risk. It may mean you're missing out on bulk pricing negotiated
with approved vendors, or worse — that you have undisclosed conflicts of interest in the
purchasing team.

In this dataset: **₦40.61 billion (13.08%)** of spend was identified as maverick or high-risk.

---

### 4.5 Foreign Exchange (FX) Exposure

**The question:** How much of our procurement is priced in US Dollars, and how badly are we hurt
when the Naira weakens?

**Why this matters:** If you buy machinery from Germany priced in USD, a weakening Naira means
the same machine costs more Naira next week than it did this week — without the vendor changing
their price at all. This is currency risk.

**How it works:** All orders where the supplier's currency is USD are isolated. The analysis
calculates:
- Total USD spend over the two-year period
- The exchange rate at the time of each order (min, max, average)
- **FX volatility** — the percentage swing between the best and worst exchange rate seen in
  the period

**What it reveals:** If the exchange rate moved from ₦800/$ to ₦1,600/$ during the analysis
window (100% volatility), a company buying $132 million worth of goods could see their Naira
cost double without any change in the underlying price negotiated with the supplier.

In this dataset: **$132.4 million USD exposure** with **99.84% FX volatility** — meaning the
exchange rate nearly doubled in this period, creating enormous budget forecasting risk.

---

## 5. How the Savings Numbers Are Calculated

The project identifies three categories of savings and totals them up:

| Savings Source | How It Is Calculated | This Dataset |
|---|---|---|
| **Price standardisation** | For each material with >10% price variance across suppliers, calculate (avg price − min price) ÷ avg price × total spend | ₦18.45B |
| **Supplier performance** | Quality incident costs (from incident log) + 3% of underperforming-supplier spend (late delivery proxy) | ₦167.47B |
| **Supplier consolidation** | 6% of spend in categories where >8 suppliers are used (fragmentation discount from volume leverage) | ₦0 (no fragmented categories in this dataset) |
| **TOTAL** | Sum of above | **₦185.92B (59.9% of spend)** |

These are **opportunity estimates**, not guaranteed outcomes. They represent the theoretical
maximum available if every recommendation is executed perfectly. The scenario analysis
(Section 7) and Monte Carlo simulation (Section 8) both apply realism filters to these numbers
to produce more credible planning ranges.

---

## 6. Supplier Scoring and Optimization

### The problem it solves

Right now, spend is distributed across suppliers historically — whoever was convenient or
available at the time. The optimization engine asks: **if we were starting fresh, knowing what
we know about each supplier's price, delivery, and quality, how should we distribute orders?**

### How supplier scoring works

Each supplier in a category gets a score from 0 to 1 on four dimensions:

| Dimension | Weight | What it measures |
|---|---|---|
| **Unit cost** | 45% | How close to the cheapest available price? Lower cost = higher score |
| **On-time delivery** | 30% | What percentage of their past deliveries arrived on time? |
| **Quality** | 15% | How low is their total financial impact from quality incidents? |
| **Risk** | 10% | Are they Low, Medium, or High risk? Low risk = full 1.0 score |

These four scores are combined into a **composite score** (a weighted average). The top
suppliers in each category are selected as the recommended supply base.

The weighting reflects a real procurement philosophy: price is the biggest driver (45%), but
reliability of delivery is also critical (30%) because a cheap supplier who's always late
costs you more in disruptions than the price saving is worth.

### Share allocation

The top suppliers in each category don't all get equal shares. Their share of the business
is proportional to their composite score. A supplier with a score of 0.85 gets roughly
twice the orders of a supplier with a score of 0.42. However, a minimum floor (15%) is
set to ensure no recommended supplier gets so little business that the relationship
becomes unviable.

### Constrained optimization

A second, stricter version of the optimization runs with hard rules (called constraints) that
cannot be violated regardless of the score:

- **No single supplier can hold more than 80% of a category** (avoids single-supplier
  dependency — if they fail, your entire production stops)
- **Categories with very high spend must have at least two suppliers** (forced dual-sourcing
  for resilience)
- **Minimum on-time delivery threshold** — any supplier below this level is automatically
  excluded from eligibility
- **Maximum quality incidents per order** — suppliers above this threshold are ineligible
- **Risk cap** — suppliers rated "High" risk can be excluded entirely with a more conservative
  setting

Three pre-configured constraint packages are provided:

| Package | Philosophy | Key differences |
|---|---|---|
| **Standard** | Balanced | Max 80% single supplier, OTD ≥ 70%, any risk level allowed |
| **Conservative** | Risk-averse | Max 65% single supplier, OTD ≥ 80%, High-risk excluded |
| **Aggressive** | Cost-focused | Max 90% single supplier, OTD ≥ 60%, fewer filters |

---

## 7. Scenarios

### Why scenarios exist

There is always uncertainty. "You could save ₦185 billion" means little if the reader doesn't
know whether that's the best case or worst case. Scenarios translate the analysis into a
**planning range** that executives can budget against.

### How scenarios work

Three scenarios — Conservative, Base, and Aggressive — apply different multipliers to the three
savings components:

| Scenario | Price Multiplier | Performance Multiplier | Consolidation Multiplier | Meaning |
|---|---|---|---|---|
| **Conservative** | 0.70× | 0.65× | 0.60× | Only 65–70% of identified savings are achievable (contracts, resistance, partial execution) |
| **Base** | 1.00× | 1.00× | 1.00× | Full identified savings (theoretical ceiling) |
| **Aggressive** | 1.20× | 1.15× | 1.25× | More savings than currently modelled (if execution is excellent and market conditions help) |

For example: if the base price standardisation saving is ₦18.45B, the conservative scenario
would plan for ₦18.45B × 0.70 = **₦12.9B** actually captured. This accounts for the reality
that not every contract can be renegotiated immediately, some suppliers will push back, and
teams take time to change their buying behaviours.

---

## 8. Risk Quantification — Monte Carlo Simulation

### What Monte Carlo simulation is (no maths required)

Imagine you want to estimate how long your commute will be tomorrow. You don't know exactly, so
you think: "usually 30 minutes, sometimes only 20 if traffic is light, sometimes 55 if there's
an accident."

A Monte Carlo simulation does the same thing for savings estimates, but instead of imagining a
few scenarios, it runs **10,000 different versions** of the future simultaneously — each one with
slightly different assumptions — and then looks at the distribution of outcomes.

### How it's applied here

Each of the three savings categories (price, performance, consolidation) has a defined
"uncertainty band":

- **Price savings** — ±15% uncertainty (price negotiations can go better or worse than the
  model assumes)
- **Performance savings** — ±20% uncertainty (harder to achieve; supplier improvement is
  gradual)
- **Consolidation savings** — ±25% uncertainty (most speculative of the three)

In each of the 10,000 runs, the model draws a random value from within each uncertainty band,
adds them up, and records the total. After all 10,000 runs, the results are sorted and presented
as percentiles:

| Percentile | What it means |
|---|---|
| **P05 (5th percentile)** | In only 5% of simulated futures would savings be this low. This is the "bad luck" floor. |
| **P25 (25th percentile)** | In 25% of futures, savings are below this number. Pessimistic-but-plausible. |
| **Median (50th percentile)** | Half the time, savings will be above this; half the time, below. Best single estimate. |
| **P75 (75th percentile)** | In 75% of futures, savings are below this. Optimistic-but-plausible. |
| **P95 (95th percentile)** | Only 5% of futures beat this. This is the "everything goes right" ceiling. |

### Why this matters to decision-makers

A CFO cannot budget against "₦186 billion maybe." But they can budget against "we are 90% confident
savings will fall between ₦X and ₦Y." The Monte Carlo output gives exactly that confidence range.

---

## 9. The Live Dashboard

The project ships with a six-page interactive dashboard accessible at
[https://procurementspendanalysis.streamlit.app/](https://procurementspendanalysis.streamlit.app/).
No login, no spreadsheets — just a browser.

### Landing Page — Procurement Spend Intelligence

The first thing a visitor sees. Four metric tiles at the top show the four headline numbers at
a glance: total spend, number of active suppliers, total savings opportunity, and maverick spend.
Below is a spend-by-category bar chart and a monthly spend trend line so leadership can see
seasonality and growth at a single glance.

### Page 1 — Executive Overview

A slightly deeper version of the landing page, designed for a weekly leadership briefing. Adds
a **scenario savings outlook chart** showing the three scenarios (Conservative, Base, Aggressive)
side-by-side as bars so the range of possible outcomes is immediately visible.

### Page 2 — Supplier Performance

Built for operations and supply chain managers. Four views:

- **Supplier scorecard table** — every supplier ranked by spend, showing their OTD percentage,
  quality cost, and letter grade
- **OTD vs quality cost scatter chart** — each bubble is a supplier; size = their spend share;
  position shows their delivery reliability (x-axis) versus quality cost burden (y-axis).
  Good suppliers cluster in the bottom-right (reliable, low quality cost)
- **Grade distribution histogram** — how many A, B, C, D suppliers exist per category
- **Top 15 suppliers by spend bar chart** — where the most money goes

### Page 3 — Savings Opportunities

Built for the procurement transformation team. Four views:

- **Price-variance opportunities bar chart** — the top 15 materials ranked by the NGN saving
  available if prices were standardised to the best-available rate
- **Optimization recommendations table** — the supplier shortlist the model produces, with
  their composite scores and recommended volume shares
- **Constrained sourcing plan** — same recommendations, but after applying the hard eligibility
  constraints (OTD floor, risk cap, dual-sourcing rule)
- **Scenario savings summary** — Conservative / Base / Aggressive numbers in a single table

### Page 4 — Risk and Uncertainty

Built for finance and risk managers. Three views:

- **Maverick and supplier-risk exposure bar chart** — total spend grouped by risk level (Low,
  Medium, High), so the risk mix is visible at a glance
- **Risk & FX KPI cards** — USD exposure, FX volatility percentage, and the three Monte Carlo
  savings bounds (P05, Median, P95) as metric tiles
- **Monte Carlo confidence table** — the full percentile breakdown of savings uncertainty from
  the simulation

### Page 5 — Data Hub

A transparency page. Lets any analyst drill into the raw data: download the source CSVs, inspect
the full procurement insights JSON, and view the underlying data tables that power all the charts.

---

## 10. Decisions That Can Be Made From This

This is ultimately why the project exists. Here is a concrete list of decisions each stakeholder
group can make with the output:

### CFO / Finance

| Decision | Page to use | Evidence provided |
|---|---|---|
| Set the procurement savings target for next year's budget | Executive Overview | Scenario range: Conservative ₦Xbn to Aggressive ₦Ybn |
| Decide how much FX hedging to buy | Risk & Uncertainty | $132M USD exposure, 99.84% FX volatility |
| Assess working capital risk from late deliveries | Supplier Performance | 58.5% of orders delivered late |
| Set confidence interval for cost savings forecasting | Risk & Uncertainty | Monte Carlo P05–P95 range |

### CPO / Chief Procurement Officer

| Decision | Page to use | Evidence provided |
|---|---|---|
| Decide which categories to renegotiate first | Executive Overview | Category spend ranked by size |
| Choose which materials to put out to tender | Savings Opportunities | Top price-variance opportunities ranked by saving |
| Decide how many suppliers to keep per category | Savings Opportunities | Optimization recommendations with composite scores |
| Set supplier performance improvement targets | Supplier Performance | Baseline OTD% and quality cost per supplier |

### Supply Chain / Operations

| Decision | Page to use | Evidence provided |
|---|---|---|
| Identify which suppliers to put on a performance improvement plan | Supplier Performance | Scatter chart showing OTD vs quality cost |
| Decide which suppliers to dual-source (reduce single-supplier risk) | Savings Opportunities | Constrained sourcing plan |
| Decide which suppliers to consider exiting | Supplier Performance | Grade D suppliers by category |

### Internal Audit / Compliance

| Decision | Page to use | Evidence provided |
|---|---|---|
| Prioritise which rogue spend cases to investigate | Risk & Uncertainty | Maverick spend by supplier and risk level |
| Set a compliance enforcement target (reduce maverick % from 13% to X%) | Risk & Uncertainty | Current maverick baseline: NGN 40.6B / 13.08% |
| Decide whether unapproved supplier use is isolated or systematic | Data Hub | Raw order-level data with supplier approval flag |

---

## 11. Real-World Impact Summary

To close the loop, here is what this analysis says, in plain language:

> Over the last two years, this company spent **₦310 billion** across 2,500 purchase orders and
> 40 suppliers. Of that spend, **₦186 billion (60%) represents money that did not need to be
> spent** if procurement decisions had been made with better information.
>
> The primary leak is not that prices are too high — it is that **the wrong suppliers are being
> used**. Suppliers who are consistently late (58.5% late delivery rate industry-wide in this
> analysis) force costly workarounds: emergency air freight, production delays, penalty clauses
> on the company's own customer contracts. Redirecting business to the suppliers that are
> already proving reliable could recover ₦167 billion of the ₦186 billion total opportunity.
>
> The remaining ₦19 billion comes from buying the same materials at wildly different prices
> from different vendors — a solvable problem through standardised purchasing policies.
>
> Additionally, **₦40 billion (13%) of spend carries unchecked risk** because it flowed to
> vendors who were never properly approved. This is not just a financial risk — it is a
> governance and reputational risk.
>
> The company also faces significant currency exposure: **$132 million of imports priced in USD**
> in a period where the exchange rate has nearly doubled — a risk that can be partially hedged
> if leadership knows it exists.

This project transforms all of that from an auditor's suspicion into a **quantified, ranked, and
visualised action plan** — ready to be taken into a board meeting, assigned to a procurement
team, and tracked to completion.

---

*Generated from `Procurement_Spend_Analysis` — a portfolio-grade analytics case study.*
*Data is synthetically generated and does not represent any real organisation.*
