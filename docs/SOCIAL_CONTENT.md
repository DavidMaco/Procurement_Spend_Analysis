# Social Content: Procurement Spend Analysis

8 LinkedIn posts, 8 Medium stories, and 8 X posts covering the full scope of this project.
Each piece is written to stand alone and can be published directly.

---

## Table of Contents

- [Post 1: The Core Problem](#post-1-the-core-problem)
- [Post 2: Where Does the Money Go? (Spend Visibility)](#post-2-where-does-the-money-go)
- [Post 3: The Overpayment Nobody Tracks (Price Standardisation)](#post-3-the-overpayment-nobody-tracks)
- [Post 4: The Hidden Cost of Supplier Underperformance](#post-4-the-hidden-cost-of-supplier-underperformance)
- [Post 5: Maverick Buying and the Governance Gap](#post-5-maverick-buying-and-the-governance-gap)
- [Post 6: Picking Suppliers with a Scoring Model](#post-6-picking-suppliers-with-a-scoring-model)
- [Post 7: The Currency Risk in Your Supply Chain](#post-7-the-currency-risk-in-your-supply-chain)
- [Post 8: Planning with Honest Uncertainty (Monte Carlo)](#post-8-planning-with-honest-uncertainty)

---

---

## POST 1: The Core Problem

---

### LinkedIn

Most procurement teams have excellent records and weak decision intelligence.

They can show you every invoice, every purchase order, every supplier payment going back five years.
The data exists. The systems are in place. The filing is meticulous.

But ask a strategic question and the conversation changes fast.

"Are we paying the same price for the same product across all our teams?"
"Which of our suppliers are costing us more in delays and defects than they're saving in unit price?"
"How much of last year's spend bypassed our approved vendor list?"

These are not complicated questions. They're just hard to answer without an analytical layer sitting
on top of your transaction history.

I built a project to close that gap.

Working with a synthetic dataset representing a Nigerian FMCG company's procurement operations
over 24 months (2,500 purchase orders, 40 suppliers, NGN 310 billion in spend), I built an
end-to-end analytics pipeline that turns raw transaction records into a ranked, quantified action
plan.

The findings were striking.

NGN 186 billion in identifiable savings sitting inside data that already existed.
NGN 40 billion spent with unapproved or high-risk vendors.
A 58% late delivery rate creating cascading production risk across the supply base.

None of this required new data collection. It required asking the data better questions.

Procurement is one of the most data-rich functions in any organisation and one of the most
analytically underdeveloped. The transaction records are gold. The question is whether anyone
is mining them.

I'll be breaking down the methodology and findings across a series of posts.
Follow along if procurement analytics, supply chain risk, or data-driven cost management is
relevant to your work.

#Procurement #Analytics #SupplyChain #DataDriven #CostOptimisation #Nigeria

---

### Medium Story

**Title: You Have the Receipts. Do You Have the Insight?**
**Subtitle: Why procurement data is everywhere but procurement intelligence is rare.**

---

There is a paradox sitting at the heart of most procurement functions.

They are among the most data-rich departments in any organisation. Every purchase order is logged.
Every invoice is filed. Every supplier interaction is recorded somewhere. If you asked a
procurement manager to prove they spent NGN 5 billion on palm oil over the last three years,
they could produce the documentation within hours.

And yet, if you asked that same manager whether they overpaid for palm oil over those three years,
most would fall silent.

Not because the information does not exist. Because nobody built the system to extract it.

**The Question Nobody Is Asking**

Most enterprise software is very good at recording and reporting. ERP systems, procurement
platforms, accounts payable tools: they tell you what happened. Purchase Order PO100042 was
placed with Supplier X on January 15 for 200 metric tonnes of sugar at NGN 48,500 per metric
tonne. The record is precise and complete.

What they do not automatically tell you is that three other teams in your organisation also bought
sugar from three other suppliers at NGN 31,000, NGN 39,000, and NGN 52,000 per metric tonne in
the same quarter. The gap between NGN 31,000 and NGN 52,000 is not a data problem. It is an
analytical problem. The data to detect it already exists. The question is whether anyone looked.

**Building the Analytical Layer**

For this project, I built a five-stage pipeline that sits on top of procurement transaction data
and converts it into decision intelligence.

Stage one is data ingestion. Four tables (suppliers, materials, purchase orders, and quality
incidents) are loaded into a structured SQLite database. The schema mirrors what any FMCG or
manufacturing company would have in a real ERP environment.

Stage two is the performance view. A SQL view calculates, for every supplier, their on-time
delivery rate, quality incident count, total financial cost of those incidents, and a performance
grade from A to D. This view recalculates every time it's queried, so it always reflects the
current data.

Stage three is the analysis engine. Eight distinct analytical routines run against the database.
Pareto spend analysis identifies where the money concentrates. Price variance detection flags
materials being purchased at inconsistent prices across suppliers. Maverick spend analysis
identifies orders placed outside the approved vendor list. FX exposure analysis quantifies the
foreign currency risk in USD-denominated orders.

Stage four is the optimisation layer. A supplier scoring model ranks each vendor on four weighted
dimensions (cost, delivery, quality, and risk) and produces a recommended shortlist for each
procurement category. A constrained version of the model adds hard eligibility rules: minimum
delivery performance thresholds, risk caps, and dual-sourcing requirements for high-value
categories.

Stage five is the output layer: an interactive Streamlit dashboard, an executive PDF report,
and PowerBI-ready CSV exports.

**What the Data Said**

Working with synthetically generated data calibrated to reflect realistic Nigerian FMCG
procurement conditions:

Total spend over 24 months: NGN 310 billion across 2,500 purchase orders and 40 suppliers.

Price standardisation opportunity: NGN 18.5 billion sitting in price variance for materials
being bought at different rates from different suppliers for no structural reason.

Supplier performance opportunity: NGN 167.5 billion in costs attributable to suppliers with
poor delivery and quality records. This number is large partly because the synthetic data was
calibrated to reflect a realistic environment where 58% of orders arrive late.

Maverick spend: NGN 40.6 billion (13% of total spend) flowing to vendors who were either
unapproved or rated as high-risk.

FX exposure: USD 132 million with 99.8% exchange rate volatility across the analysis window,
representing a major unhedged budget risk.

Total identified savings: NGN 186 billion, representing 60% of total spend over the period.

**Why the Numbers Are Not the Point**

These figures are large partly because the dataset was designed to surface clear patterns. In a
real-world engagement, the percentages would likely be smaller and the paths to capture savings
would be longer.

But the methodology translates directly.

Every FMCG company buys the same materials from multiple suppliers. Some of those suppliers are
cheaper, faster, and more reliable than others. In most organisations, buying decisions are driven
by habit, convenience, or individual relationships rather than systematic performance data. The
result is that better options exist in the vendor base and nobody is consistently routing business
to them.

An analytical layer that scores every supplier on objective criteria and routes spend accordingly
is not a complicated idea. It is a straightforward application of data that already exists.

The complicated part is building the discipline to use it.

**What This Project Enables**

The live dashboard at procurementspendanalysis.streamlit.app lets any executive navigate five
pages of insight: spend by category, supplier performance rankings, price-variance opportunities,
risk exposure, and confidence-bounded savings projections.

No spreadsheets. No coding. Filters by category and date range. Downloadable data for anyone
who wants to go deeper.

The core message: if your organisation has years of procurement transaction data and is not
systematically mining it for savings intelligence, the receipts are only doing half their job.

---

### X Post (Thread)

**Tweet 1/5**
Most procurement teams can show you every invoice going back 5 years.

Ask them if they overpaid for anything. The conversation stops.

Not because the data doesn't exist. Because nobody asked it the right questions.

Thread on what I built to fix that.

**Tweet 2/5**
I built a procurement analytics pipeline on a synthetic FMCG dataset.

2,500 purchase orders. 40 suppliers. NGN 310 billion in spend. 24 months.

The question: what does the data know that the procurement team doesn't?

**Tweet 3/5**
What we found:
- NGN 186B in savings opportunities
- NGN 40B to unapproved/high-risk vendors
- 58% late delivery rate across the supplier base

All of it was hiding inside data the company already had.

**Tweet 4/5**
The pipeline:
1. Raw data into a structured database
2. Supplier performance scoring
3. 8 analytical routines (spend, price, risk, FX)
4. Supplier optimisation engine
5. Live Streamlit dashboard

**Tweet 5/5**
Procurement is data-rich and analytically underdeveloped in most organisations.

You don't need more data. You need better questions, and a system that can answer them.

Live: procurementspendanalysis.streamlit.app

---

---

## POST 2: Where Does the Money Go?

---

### LinkedIn

Before you can optimise anything, you have to know where the money is going.

This sounds obvious. In practice, most companies have a very rough sense of procurement spend
by category. They know the big buckets. What they don't know is the exact breakdown, how it
has shifted over time, and where the highest leverage for cost reduction sits.

The first thing my procurement analytics pipeline does is answer the "where does the money go"
question precisely.

Using a Pareto analysis across 2,500 purchase orders covering NGN 310 billion in spend, the
data groups all transactions by procurement category and calculates the percentage each category
contributes to total spend. This is not complex maths. But doing it consistently, across every
transaction, over 24 months, produces insights that gut feel never surfaces.

The Pareto principle holds in procurement as reliably as it holds everywhere else. A small
number of categories account for most of the spend. And the implication is direct: concentrate
your cost-reduction work on the categories that move the total number most.

A 5% price reduction in your top spend category saves more Naira than a 15% reduction in your
smallest category.

Once you know where the money concentrates, you can direct analytical resource (and negotiating
resource, and supplier management resource) proportionally. Without this baseline, cost
optimisation efforts get scattered across categories based on whoever shouts loudest rather
than where the real leverage is.

The Pareto chart is always the first page of every procurement review I run. Not because it's
sophisticated. Because everything else depends on it.

#Procurement #SpendAnalysis #SupplyChain #Analytics #ProcurementStrategy

---

### Medium Story

**Title: The First Question Every Procurement Leader Should Be Able to Answer**
**Subtitle: Why spend visibility by category is the foundation of every procurement strategy.**

---

There is a question that should sit at the top of every procurement leader's weekly briefing.

Not "did we hit budget?" and not "are our suppliers performing?" Both of those are important.
But neither is the first question. The first question is simpler: where is the money actually
going?

This sounds trivial until you try to answer it precisely.

**Why Spend Visibility Is Harder Than It Looks**

In theory, every purchase order is recorded. The data exists. But "the data exists" and "the
data is instantly usable for strategic decisions" are very different things.

Transaction data sits in ERP systems designed for operational processing, not strategic
analysis. Pulling a clean, categorised view of spend across 2,500 purchase orders and four
procurement categories over 24 months requires writing queries, structuring the results, and
presenting them in a form that is actually interpretable by a decision-maker.

This is not technically difficult. It is just work that most procurement functions deprioritise
because the operational day-to-day crowds it out.

**The Pareto Principle in Procurement**

The Pareto principle says that roughly 80% of outcomes come from 20% of causes. In procurement,
this translates reliably: a small number of spend categories account for the overwhelming
majority of total procurement cost.

For any company buying raw materials, packaging, equipment, and services, the Raw Materials
category typically consumes 60 to 70% of total procurement spend. The implication is direct.

If you have limited analytical resource and limited negotiating bandwidth, you do not allocate
it equally across all categories. You concentrate it where the spend concentrates.

A 5% reduction in a category representing 65% of your spend recovers 3.25% of total
procurement cost. A 5% reduction in a category representing 8% of spend recovers 0.4% of total
cost. The effort for each negotiation is roughly similar. The financial outcome is not.

**What the Data Shows**

In the synthetic FMCG dataset underlying this project, the Pareto structure is very clear when
you run the analysis. Each category's share of total spend is calculated as:

Total spend in category divided by total spend across all categories, multiplied by 100.

The result is a ranked breakdown that tells a procurement director exactly which categories
deserve the most intense spend management. Without this view, procurement strategy tends to
be driven by whoever is generating the most complaints, the most urgent requests, or the most
visible problems rather than where the financial leverage actually sits.

**From Visibility to Action**

Spend visibility by category is not the end of the analysis. It is the foundation.

Once you know that Raw Materials represents 65% of your procurement spend, the natural next
questions are: are we getting competitive pricing for Raw Materials? Are our Raw Materials
suppliers reliable? How fragmented is our Raw Materials supply base?

These questions lead directly to the deeper analytical modules in this project: price variance
analysis, supplier performance scoring, and supplier consolidation opportunity assessment.

The Pareto chart is always the starting point because it tells you where to spend your
analytical energy first. Every subsequent module in the pipeline is informed by the category
concentration revealed in step one.

**The Dashboard View**

In the live Streamlit dashboard for this project, the first visual on every page is a
spend-by-category bar chart that shows both the absolute spend and the percentage share for
each category. A monthly trend line below it shows how the category mix has shifted over time.

These two charts together answer the spend visibility question in about three seconds. They are
not impressive visualisations. They are the correct starting point for any procurement
discussion anywhere.

The lesson is not sophisticated. Spend visibility is foundational. Do not skip it to get to the
"interesting" analysis. The interesting analysis is only interesting if you know where the
leverage is.

---

### X Post (Thread)

**Tweet 1/4**
Before you can optimise procurement spend, you have to know where it goes.

Sounds obvious. Most companies only have a rough sense.

Here's why precise spend visibility changes everything.

**Tweet 2/4**
I ran a Pareto analysis on 2,500 purchase orders across 4 categories (NGN 310B total).

The result: a small number of categories account for most of the spend.

That breakdown tells you where to direct every negotiation and every analytical effort.

**Tweet 3/4**
A 5% saving on a category that's 65% of your spend recovers 3.25% of total cost.

A 5% saving on a category that's 8% of spend recovers 0.4%.

Same effort. Completely different outcome.

**Tweet 4/4**
Spend visibility is not sophisticated analytics. It's the foundation for all of it.

Without knowing where the money goes, cost optimisation gets allocated to whoever shouts
loudest instead of where the leverage is.

---

---

## POST 3: The Overpayment Nobody Tracks

---

### LinkedIn

Here is a scenario that plays out quietly in almost every large organisation.

Team A buys stainless steel drums from Supplier X at NGN 45,000 per unit.
Team B buys the same drums from Supplier Y at NGN 71,000 per unit.
Team C buys them from Supplier Z at NGN 59,000 per unit.

No one overstepped their authority. All three followed the right internal processes.
But the organisation just paid 58% more than it needed to for the exact same product.

This is what price standardisation analysis finds. And it is more common than most finance and
procurement teams would like to admit.

In the procurement analytics pipeline I built, price variance detection runs across every
material that was purchased from more than one supplier. For each material, we calculate the
minimum price paid, the average price paid, and the gap between them. Any material where the
average price paid is more than 10% above the minimum available price gets flagged, and the
recoverable saving is quantified.

The formula is straightforward. Potential saving equals (average price minus minimum price)
divided by average price, multiplied by total spend on that item.

Across a synthetic FMCG dataset with NGN 310 billion in spend, this analysis identified
NGN 18.45 billion in price standardisation savings. That is money that could be recovered
simply by directing all orders for each material to the cheapest qualified supplier, or by
renegotiating the whole category to the best available market rate.

The reason this pattern persists in most organisations is not that procurement teams are
negligent. It is that without a tool that looks across all transactions simultaneously, the
inconsistency is invisible. Each team sees their own orders. Nobody sees the comparison.

That comparison is the entire value of this analysis.

#Procurement #PriceAnalysis #CostReduction #SpendManagement #Analytics

---

### Medium Story

**Title: The Invisible Overpayment: How Price Inconsistency Silently Drains Procurement Budgets**
**Subtitle: A walk through price standardisation analysis and what it surfaces.**

---

Most organisations pay several different prices for the same product without ever realising it.

This is not unusual. It is not even a sign of poor procurement management. It is a natural
consequence of decentralised purchasing at scale. Multiple teams, multiple relationships,
multiple suppliers, all operating independently. The result is that the same item appears on
invoices at four different prices in the same quarter, and until someone looks at all four
invoices simultaneously, nobody knows.

Price standardisation analysis is the tool that looks at all four simultaneously.

**How the Analysis Works**

The logic is straightforward, which is part of why it is so powerful.

For every material or service in the procurement database, we look at every purchase order
where that material was bought from more than one supplier. Then we calculate three numbers:

The minimum price paid for any unit of that material in the analysis period. This is the
best rate the organisation already achieved, with at least one supplier, for this exact product.
The average price paid across all purchases of that material. This is what the company is
actually paying on average.
The gap between the two, expressed as a percentage.

If the average price is more than 10% higher than the minimum price, the item is flagged. The
10% threshold is deliberate. Small variation in prices is normal and can reflect genuine
differences like delivery location, order size, or quality specifications. Variation above 10%
typically indicates an opportunity to standardise.

The potential saving is then calculated as:

(Average price minus minimum price) divided by average price, multiplied by total spend on
that item.

This represents how much the organisation would have saved if all purchases had been made at
the best available price. It is the upper bound of the opportunity. In practice, a well-run
price standardisation programme captures 60 to 80% of the theoretical maximum.

**What the Analysis Does Not Mean**

It is worth being clear about what this analysis is not saying.

It is not saying that the cheapest supplier for a given material is automatically the best
choice. A supplier who charges 10% less per unit but delivers 20% of orders late, or generates
a high volume of quality incidents, may actually be the more expensive option once the full cost
of their underperformance is factored in.

Price standardisation analysis should always be run alongside supplier performance analysis, not
instead of it. The goal is not to route all business to the cheapest supplier regardless of
quality. The goal is to identify where significant price variation exists, understand why it
exists, and close the gap where the underlying reasons do not justify it.

**What the Numbers Look Like**

In the synthetic FMCG dataset underlying this project, NGN 18.45 billion in price
standardisation savings was identified across the materials with significant price variance.

The top opportunities surface materials where multiple suppliers are being used and the price
spread is large. A material bought from five suppliers at prices ranging from NGN 30,000 to
NGN 85,000 per unit has enormous standardisation potential. A material bought from three
suppliers within a NGN 43,000 to NGN 48,000 range has much less.

The analysis ranks all materials by the NGN value of their standardisation opportunity. This
ranking directly tells the procurement team where to focus renegotiation energy. The materials
at the top of the list are where a one-time negotiation exercise has the highest financial
payoff.

**Turning the Analysis into Action**

Once the ranked list is available, the procurement action plan writes itself.

For each high-opportunity material, the decision is: do we consolidate purchasing to the
cheapest qualified supplier, or do we renegotiate the entire supply base down to the benchmark
price? The right answer depends on whether the cheapest supplier has the capacity and
reliability to handle more volume.

This is why the price variance analysis in this project is displayed alongside the supplier
performance scorecard. A material with high price variance and a low-cost supplier who scores
highly on delivery and quality is an easy consolidation decision. A high-variance material
where the cheapest supplier is unreliable requires a different approach: renegotiate with the
reliable suppliers to bring their price closer to the benchmark.

In either case, the analysis surfaces the opportunity. The procurement team makes the call.

**The Broader Point**

Price inconsistency is a symptom, not a disease. It appears in organisations that have grown,
that have acquired other businesses, that have allowed departmental autonomy without
category visibility, or that have simply never looked at the comparison.

Treating it requires visibility first. The price variance chart is that visibility. Once it
exists, the pattern that was invisible to everyone in the organisation becomes obvious to anyone
who looks.

That is the full value of this analysis, delivered in a single ranked bar chart.

---

### X Post (Thread)

**Tweet 1/4**
Here's a quiet problem that lives inside almost every large organisation:

Team A pays NGN 45,000/unit for a product.
Team B pays NGN 71,000/unit for the same product.

No one did anything wrong. But the company just overpaid by 58%.

**Tweet 2/4**
This is what price standardisation analysis finds.

For every material bought from more than one supplier, we calculate:
- Minimum price paid (your best rate)
- Average price paid (what you're actually paying)
- The gap

**Tweet 3/4**
If the average is more than 10% above the minimum, it's flagged.

The potential saving = (avg price - min price) / avg price x total spend on that item.

Across NGN 310B in procurement spend, this found NGN 18.5B.

**Tweet 4/4**
The reason this persists: each team sees their own orders. Nobody sees the comparison.

That comparison is the entire value of the analysis.

One ranked chart. Clear action list. No new data required.

---

---

## POST 4: The Hidden Cost of Supplier Underperformance

---

### LinkedIn

A supplier who charges 10% less per unit is not automatically the cheaper supplier.

This is counterintuitive when you first encounter it. Unit price is visible. It's on the
invoice. The cost of a late delivery is not on any single document. It shows up indirectly,
across your production schedule, your logistics costs, your customer penalties for late orders.

In procurement analytics, the real cost of a supplier is unit price plus performance cost.
And in most analyses I've run, performance cost dwarfs unit price variation.

Here's how the analysis quantifies it.

Two components are calculated for underperforming suppliers (those with on-time delivery below
80% or more than two quality incidents in the period):

Quality cost: directly measured from the incidents log. Each quality problem has a financial
impact recorded, covering defect remediation, returns, write-offs, and testing costs.

Delivery cost: estimated at 3% of total spend with each underperforming supplier. This
represents the documented industry cost of late delivery: expedited freight, production line
downtime, and penalties on the company's own customer contracts.

In the synthetic FMCG dataset I modelled, the combined performance improvement opportunity
was NGN 167.47 billion. This is nearly 10 times the price standardisation saving
(NGN 18.45 billion). It is the dominant savings lever by a significant margin.

The practical implication: before you spend six months renegotiating prices, find out which
suppliers are consistently disrupting your operations. Replacing or reforming the worst
performers will likely recover more cost in less time.

Price negotiation is visible. Supplier performance management is where the real money is.

#SupplierManagement #Procurement #SupplyChainRisk #Analytics #CostManagement

---

### Medium Story

**Title: The Supplier That Seems Cheap Is Not Always the Supplier That Is Cheap**
**Subtitle: Why delivery and quality failures are financial failures, and how to quantify them.**

---

There is a common trap in procurement: optimising for the number that is easiest to measure.

Unit price is easy to measure. It is on every invoice. It can be compared across suppliers
with a simple spreadsheet. It is also the most visible number in any supplier negotiation.

The problem is that unit price only tells you what you paid at the point of transaction. It
does not tell you what you paid over the life of the relationship. A supplier who is
consistently late does not charge you extra for the production line downtime your factory
incurs when their delivery is three days behind. A supplier whose quality is unreliable does
not invoice you for the cost of rejecting a shipment, the time your quality team spends on
inspection, or the expedited replacement order you had to place. These costs are real. They
are just not visible in the same place as the unit price.

Supplier performance analysis is the practice of making them visible.

**The Two Components of Performance Cost**

Every underperforming supplier generates two categories of cost beyond their invoice.

The first is quality cost. This is the most directly measurable. Quality incidents, whether
they are product defects, out-of-specification materials, or contamination events, generate
traceable financial impact: the cost of returning or scrapping defective goods, the testing
and inspection labour, the production batch that had to be destroyed, the emergency replacement
procurement. In the procurement database underlying this project, every quality incident is
recorded with a cost impact field. Summing these across underperforming suppliers gives a
direct financial figure.

The second is delivery cost. This is more indirect but no less real. When a supplier delivers
late, the downstream effects include production schedule disruption, idle labour time when a
production line cannot run because a key input has not arrived, expedited shipping costs for
emergency replacement orders, and in some cases, penalty clauses on the company's own customer
contracts for late deliveries. Industry research consistently estimates these costs at 3 to 5%
of the total spend with the late supplier. In this analysis, 3% is used as a conservative
estimate.

The performance cost for each underperforming supplier is the sum of these two components.

**The Scale of the Opportunity**

In the synthetic FMCG dataset underlying this project, 58.47% of all purchase orders were
delivered late across the supply base. This is an extremely high rate. It means that for
roughly six out of every ten orders placed, the receiving company had to absorb some level of
production disruption.

The combined performance improvement savings opportunity calculated from this analysis was
NGN 167.47 billion. This is not the cost of the late deliveries themselves. It is the estimated
financial recovery available if the underperforming portion of the supply base were replaced
with suppliers performing at the level of the best quartile in the current base.

To put this in perspective: the price standardisation opportunity in the same dataset was
NGN 18.45 billion. Performance improvement is roughly nine times larger.

**Why This Pattern Is So Common**

Most procurement organisations spend more time managing supplier prices than managing supplier
performance. This makes sense from a measurement perspective: prices are easy to compare,
negotiations are straightforward to conduct, and savings are immediately visible in unit cost
reductions.

Performance management is harder. It requires sustained data collection across deliveries and
quality events. It requires a willingness to have difficult conversations with suppliers who may
have long relationships with the business. It requires the organisational will to switch
suppliers when performance does not improve, even if the incumbent has a lower unit price.

Many organisations do some version of supplier performance tracking. Fewer translate those
performance metrics into financial impact. And very few use the financial impact to rank
suppliers for replacement or remediation.

This analysis does all three.

**The Supplier Scorecard**

For every supplier in the database, the performance view calculates: total order count,
on-time delivery percentage, quality incident count, total quality cost, and a composite
performance grade (A, B, C, or D).

The scatter chart in the dashboard plots every supplier on two axes: delivery reliability
(horizontal) and quality cost burden (vertical). Suppliers in the bottom-right quadrant are
reliable and cheap to manage. Suppliers in the top-left quadrant are unreliable and expensive.
Bubble size indicates their share of total spend.

Any supplier whose bubble is large, positioned top-left, and graded C or D is a priority for
a supplier performance improvement plan or a replacement evaluation.

The analysis does not make the decision. It makes the decision obvious.

---

### X Post (Thread)

**Tweet 1/5**
A supplier who charges 10% less per unit is not always the cheaper supplier.

Here's the trap most procurement teams fall into.

**Tweet 2/5**
Unit price is on the invoice. You can see it and compare it easily.

The cost of a late delivery is not on any single document. It shows up across your production
schedule, logistics, customer penalties.

**Tweet 3/5**
Performance cost has two components:
1. Quality cost (defects, returns, write-offs) - measured directly from incident records
2. Delivery cost (production disruption, expedited freight) - estimated at 3% of spend

**Tweet 4/5**
In the FMCG dataset I modelled:
- Price standardisation saving: NGN 18.5B
- Supplier performance saving: NGN 167.5B

Performance management is 9x the price negotiation opportunity.

**Tweet 5/5**
Most procurement teams spend more time on price negotiation than supplier performance.

The data consistently says that's the wrong priority.

---

---

## POST 5: Maverick Buying and the Governance Gap

---

### LinkedIn

Maverick buying is the procurement version of a slow leak.

No single transaction looks alarming. A project manager needs equipment urgently and uses a
vendor their old colleague recommended. A logistics coordinator finds a cheaper option on a
trading platform and skips the approval process because "it's just a small order." A factory
manager places an order with a local supplier because the approved vendor has a three-week
lead time and production cannot wait.

Each of these decisions, taken in isolation, is at least understandable. Aggregated across two
years of operations, they become a governance problem that carries real financial and
reputational risk.

In the procurement analytics pipeline I built, maverick spend analysis cross-references every
purchase order against the approved vendor list. Any order placed with a supplier who is either
not formally approved, or who carries a "High" risk rating, is flagged as maverick spend.

Across the synthetic FMCG dataset underlying this project, NGN 40.61 billion (13.08% of total
spend) was classified as maverick.

That 13% matters for several reasons.

Financially, maverick spend bypasses the negotiated rates and contractual protections that sit
on the approved vendor list. You likely paid more than you needed to.

From a risk perspective, unapproved vendors have not been vetted for financial stability,
regulatory compliance, quality standards, or ethical sourcing practices.

From a governance perspective, 13% of spend flowing outside formal process is a finding that
any auditor or board risk committee will want to understand.

The analysis does not assume that every maverick purchase was a bad decision. Sometimes the
approved vendor genuinely cannot deliver and a pragmatic off-list choice is the right call.
What it does is make the scale of the pattern visible, so leadership can decide whether it is a
management issue, a process design issue, or an approved vendor list that needs updating.

Visibility first. Judgement second.

#Procurement #Compliance #SupplyChainRisk #InternalAudit #GovernanceRisk

---

### Medium Story

**Title: The 13% Problem: Maverick Spending and the Governance Gap in Procurement**
**Subtitle: Why unapproved vendor spend is about more than compliance.**

---

Most procurement policies have an approved vendor list.

The process is usually well-intentioned. Vendors go through a vetting process covering
financial health, regulatory standing, quality certifications, insurance coverage, and sometimes
sustainability and ethical sourcing criteria. Once approved, they go on the list. Employees are
expected to buy from the list.

In practice, the list is often observed selectively.

Production is shutting down and the approved cold storage film supplier cannot deliver for
eight days. A factory manager finds a local alternative, places the order, and files the
paperwork after the fact. A procurement coordinator knows a reliable vendor from a previous
job that isn't on the current list and uses them for a routine order. A project team is under
budget pressure and finds a cheaper option on a trading platform that is faster to access than
the internal procurement portal.

None of these people are necessarily acting in bad faith. They are making practical decisions
under pressure. The aggregate effect, multiplied across dozens of people and hundreds of
decisions over two years, is a significant portion of total spend flowing outside formal
process.

**How Maverick Spend Is Identified**

The analysis is structurally simple.

Every purchase order in the database has a supplier_id that can be joined back to the suppliers
table. The suppliers table has two relevant fields: is_approved (a boolean indicating whether
the vendor went through formal vetting) and risk_level (Low, Medium, or High).

A purchase order is classified as maverick if the supplier is either not approved, or carries
a High risk rating. The total spend across all maverick orders is summed, and the result is
expressed both as a currency amount and as a percentage of total procurement spend.

The output is a ranked list of maverick suppliers by spend. This is deliberately designed as a
ranked list because the follow-up action differs by tier.

**What to Do With the Finding**

The ranked maverick supplier list enables three distinct decisions.

The first decision is whether to onboard the supplier formally. For a supplier appearing
repeatedly on the maverick list, where the spend volume is significant, the right response may
simply be to run them through the formal vetting process. If they pass, they join the approved
list and the spend stops being maverick. The practical use of this particular vendor is
validated, and the governance gap is closed.

The second decision is enforcement. For maverick spend that is genuinely outside policy, and
where the purchasing decisions cannot be justified by emergency or approved vendor failure, the
finding becomes input for an internal audit review. At 13% of total spend, the scale makes
it a board-level governance matter.

The third decision is process redesign. Sometimes high maverick spend is a signal that the
approved vendor list is too narrow, that lead times with approved vendors are too long, or
that the procurement approval process is too slow for operational needs. If employees are
consistently bypassing process under legitimate operational pressure, the process may need
redesign rather than just enforcement.

**Beyond the Numbers**

The NGN 40.61 billion maverick figure in this analysis is significant partly because the
synthetic dataset was seeded with a realistic rate of non-approved vendor use. The more
important point is the structure of the finding.

Maverick spend is always traceable if the data is set up correctly. The approved status and
risk classification sit in the supplier master. The purchase order history connecting
transactions to suppliers is always present. The analysis requires no new data collection.
It requires a query that nobody ran before.

This is the pattern that repeats across every module in this project. The information existed.
The analysis was not being done because no one had built the tool to do it.

**What the Dashboard Shows**

In the Risk and Uncertainty page of the Streamlit dashboard, maverick spend is shown as a bar
chart grouped by risk level: Low, Medium, and High. The chart immediately shows the risk mix
of the off-list spend. Is most of the maverick spend with Low-risk vendors (pragmatic, low
urgency), or is a meaningful portion going to High-risk vendors with no vetting history?

The answer shapes the urgency of the response. High-risk, high-volume maverick spend is a
governance emergency. Low-risk, moderate-volume maverick spend is a process improvement
opportunity.

The chart makes that distinction visible in about three seconds.

---

### X Post (Thread)

**Tweet 1/4**
Maverick buying is the procurement version of a slow leak.

No single transaction looks alarming. A project manager uses a convenient vendor. A
coordinator skips approval because it's "just a small order."

Multiply that across two years.

**Tweet 2/4**
In the procurement dataset I analysed:
NGN 40.6 billion (13.08% of total spend) flowed to unapproved or high-risk vendors.

Not through fraud. Through pressure, convenience, and process gaps.

**Tweet 3/4**
The analysis cross-references every PO against the approved vendor list.

Flag: is_approved = False OR risk_level = 'High'.

Result: a ranked list of maverick suppliers, sorted by spend.

**Tweet 4/4**
What to do with the finding:
1. Onboard recurring vendors formally (if they'd pass vetting)
2. Enforce policy with audit review (if spend is genuinely off-policy)
3. Redesign the process (if employees bypass it under legitimate pressure)

Visibility first. Judgement second.

---

---

## POST 6: Picking Suppliers with a Scoring Model

---

### LinkedIn

Most supplier selection decisions are made on a combination of precedent, relationship, and
price. Whoever supplied similar things before, brought a good relationship to the table, and
quoted competitively usually wins the business.

There is nothing wrong with this as a starting point. The problem is that it doesn't scale,
it doesn't update as performance data accumulates, and it tends to lock in decisions that
made sense once but no longer reflect reality.

A supplier scoring model does something different. It takes the data you already have about
every supplier's performance, structures it into four objective dimensions, weights those
dimensions by their strategic importance, and produces a numerical ranking that can be
regenerated whenever circumstances change.

In the procurement analytics pipeline I built, every supplier is scored on:

Cost (45% weight): how close is their unit price to the cheapest available option in this
category? This is the largest weight because cost efficiency is the primary mandate of
procurement.

Delivery reliability (30% weight): what percentage of their orders arrived on time? Delivery
reliability gets the second-largest weight because unreliable delivery generates hidden costs
that can exceed the unit price benefit.

Quality (15% weight): how low is their total financial impact from quality incidents? Lower
cost impact equals a higher quality score.

Risk (10% weight): are they classified as Low, Medium, or High risk? Low risk suppliers
receive the full score.

The top-ranked suppliers in each category are selected as the recommended supply base, and
their share of the business is allocated proportionally to their composite score.

This approach does three things that gut-feel supplier management does not. It is transparent
(anyone can see exactly why a supplier was ranked where they were). It is updateable
(re-running the model with six more months of performance data produces a fresh ranking).
And it separates the analytical decision from the relationship decision, which protects the
procurement team from making choices they cannot defend to an auditor.

The model is a recommendation, not a mandate. Humans make the final call.
But the final call is much easier to make when the data has already done the scoring.

#Procurement #SupplierManagement #Analytics #DecisionMaking #SupplyChain

---

### Medium Story

**Title: How to Choose the Right Suppliers Without It Becoming Complicated**
**Subtitle: A practical walkthrough of weighted supplier scoring and what it produces.**

---

Supplier selection is one of the most consequential decisions a procurement function makes.

The right suppliers determine your cost base, your supply chain resilience, your product
quality, and your organisation's exposure to ethical and regulatory risk. Most companies
acknowledge this. Fewer have a systematic methodology for making these decisions that is
consistent, repeatable, and defensible.

A weighted scoring model is one of the most useful and underused tools in procurement. Here is
how it works in practice.

**The Problem with Informal Selection**

When supplier selection is informal, several predictable problems emerge.

The first is incumbency bias. The supplier who won the business three years ago keeps winning
it because switching requires effort and switching costs are visible while the cost of
staying with a declining performer is diffuse and hard to measure.

The second is relationship capture. A supplier with strong personal relationships with
purchasing staff consistently outperforms equally qualified competitors in selection processes
because the selection criteria are loosely defined and interpersonal trust fills the gap.

The third is single-metric optimisation. Because price is the most visible and measurable
criterion, it becomes the dominant decision criterion. Suppliers who are cheap but unreliable
win business over suppliers who are slightly more expensive but operationally excellent.

A scoring model addresses all three by making the criteria explicit before the selection
decision is made.

**The Four Dimensions**

In this project's supplier scoring engine, four dimensions are used, each with a defined weight.

Cost efficiency (45% weight). Each supplier's average unit cost is normalised against the
range of unit costs in the category. The cheapest supplier in the category scores 1.0. The
most expensive scores 0.0. Suppliers in between are scored proportionally. Cost gets the
highest weight because it is the primary mandate of procurement as a function.

Delivery reliability (30% weight). Each supplier's on-time delivery percentage, calculated
from historical order data, is normalised across the category's range. A supplier with 95%
on-time delivery scores near 1.0. A supplier with 55% on-time delivery scores near 0. This
is the second-highest weight because delivery failure generates indirect costs that often
exceed unit price variation in total financial impact.

Quality (15% weight). Each supplier's total financial impact from quality incidents is
normalised in inverse (lower quality cost means higher score). This dimension receives a
lower weight because quality incidents are less frequent than delivery events and are partly
also captured in the delivery score when they cause shipment delays.

Risk (10% weight). Risk level (Low, Medium, or High) is converted to a numerical score
(Low = 1.0, Medium = 0.6, High = 0.2). Risk receives the lowest weight because it is a
floor condition rather than a differentiating factor: very high-risk suppliers should be
excluded from consideration entirely through the constraint layer.

**How the Composite Score Works**

The composite score is a weighted average of the four dimension scores:

Composite = (Cost score x 0.45) + (Delivery score x 0.30) + (Quality score x 0.15) + (Risk
score x 0.10)

A supplier who is the cheapest in their category, delivers on time every time, has no quality
incidents, and is Low risk would score 1.0. In practice, no supplier is perfect across all
dimensions. The model finds the best overall balance.

**Share Allocation**

Rather than giving all business to the top-ranked supplier, the model allocates volume shares
proportionally to composite scores. This avoids single-supplier dependency while still
concentrating more business with better performers.

A minimum share floor (15%) ensures that no selected supplier receives such a small allocation
that maintaining the relationship is economically unviable for them.

**The Constrained Version**

A second version of the model applies hard eligibility constraints before scoring runs. Suppliers
below a minimum on-time delivery threshold are excluded entirely. Suppliers above a maximum
quality incident rate are excluded. Suppliers above a maximum risk level are excluded.

This two-stage approach separates "eligible to bid" decisions (handled by constraints) from
"who gets how much" decisions (handled by the scoring model). The result is a supplier
shortlist that is both analytically rigorous and practically implementable.

**What the Model Is Not**

The scoring model is a recommendation engine, not a decision-maker. It surfaces the analytical
case for a particular supplier allocation. A procurement leader might override a recommendation
because of a long-term strategic partnership, a transition that would take 18 months to manage
safely, or market intelligence not captured in the historical data.

That is fine. The model's job is to make the analytical case transparent and quantified, so
that any override is a deliberate choice rather than a default. The question changes from "who
should we use?" to "do we have a good reason not to follow the model's recommendation?"

---

### X Post (Thread)

**Tweet 1/5**
Most supplier choices are made on: precedent, relationship, and price.

This makes sense in the moment. At scale, it creates three problems:
- Incumbency bias
- Relationship capture
- Single-metric optimisation (price only)

**Tweet 2/5**
A supplier scoring model fixes this.

4 dimensions, each with a weight:
- Cost efficiency: 45%
- Delivery reliability: 30%
- Quality: 15%
- Risk: 10%

**Tweet 3/5**
Why weight it this way?

Cost is the primary mandate of procurement (45%).
But delivery failure generates hidden costs that often exceed unit price savings (30%).
Quality issues are less frequent but financially significant (15%).
Risk is a floor condition, not a differentiator (10%).

**Tweet 4/5**
The composite score = weighted average across the 4 dimensions.

Top suppliers get selected. Volume is distributed proportionally to score.
Minimum 15% floor so no supplier gets too small a share to maintain.

**Tweet 5/5**
The model is a recommendation, not a mandate.

But "do we have a good reason NOT to follow the data?" is a much better question
than "who should we use?"

---

---

## POST 7: The Currency Risk in Your Supply Chain

---

### LinkedIn

Foreign exchange risk is one of the least-discussed cost drivers in procurement.

Not because it is small. Because it is invisible until it is very large.

When you buy materials from a German machinery supplier priced in USD, your procurement team
negotiates a unit price in dollars. That price might look competitive and remain competitive for
months. But if the Naira depreciates against the Dollar by 30% between the time you signed the
contract and the time you process the invoice, you just paid 30% more in Naira than your budget
assumed, without the German supplier changing anything.

FX exposure sits quietly in every procurement portfolio that includes international suppliers.
In Nigeria, where the Naira-to-Dollar rate has moved dramatically over recent years, this
exposure is particularly material.

In the procurement analytics pipeline I built, FX exposure analysis isolates all purchase
orders denominated in USD and calculates three things:

Total USD spend across the analysis window. This is the headline exposure: how much of the
procurement portfolio is subject to currency movement.

Exchange rate range. The minimum and maximum NGN/USD rate observed during the period. This
range shows how much the cost of the same product varied simply due to currency movement.

FX volatility. The percentage difference between the best and worst exchange rate seen. This
is the risk measure: a 99.8% volatility means the exchange rate nearly doubled in the analysis
window.

In the synthetic FMCG dataset I modelled, this analysis found USD 132 million in FX-exposed
procurement spend with 99.8% exchange rate volatility.

This is the kind of number that prompts a finance director to ask: do we have a hedging policy
for procurement FX? And if not, why not?

Data visibility is the prerequisite for that conversation. The conversation cannot happen if
nobody has pulled the number.

#Procurement #FXRisk #SupplyChainFinance #CurrencyRisk #Nigeria

---

### Medium Story

**Title: The Currency Risk Your Procurement Team Is Not Measuring**
**Subtitle: FX exposure in supply chains and why it belongs on every procurement dashboard.**

---

Of all the risks carried in a procurement portfolio, foreign exchange exposure may be the
least systematically monitored.

This is not because it is small. In any import-dependent supply chain, and particularly in
markets like Nigeria where the currency has experienced significant volatility, FX exposure
can be larger than the combined cost of price inefficiency and supplier underperformance. It
receives less attention because it occurs outside the nominal procurement process. The
procurement team negotiated a fair price in dollars. The finance team processes the payment
in Naira. Neither team owns the exposure completely, and as a result, neither team manages
it proactively.

This gap is what FX exposure analysis in the procurement analytics pipeline is designed to
close.

**How FX Exposure Works in Practice**

When a Nigerian FMCG company buys processing equipment from a German manufacturer, the
contract is typically denominated in US Dollars. The procurement team focuses on the dollar
price. At the time of negotiation, the dollar price may represent excellent value at the
prevailing exchange rate.

Six months later, when the equipment is delivered and the invoice lands, the Naira may have
weakened significantly. The dollar price on the invoice is identical to what was negotiated.
The Naira cost is substantially higher. Nobody made a mistake. The market moved.

If the company buys USD 132 million worth of materials and equipment across 24 months, and
the exchange rate goes from NGN 800 per dollar to NGN 1,600 per dollar in that period, the
Naira cost of that procurement doubles without a single supplier raising their prices.

This is not a hypothetical. The synthetic dataset underlying this project was calibrated to
reflect realistic exchange rate movement in the Nigerian market over recent years.

**What the Analysis Calculates**

The FX exposure module in the analysis pipeline does three things.

First, it isolates all purchase orders where the supplier's currency is US Dollars. These are
the orders that carry exchange rate risk. NGN-denominated orders carry no FX exposure.

Second, for each USD order, both the total amount in USD and the effective exchange rate at
the time of the transaction (calculated as total NGN divided by total USD) are captured. This
produces a time series of exchange rates across all USD purchases in the analysis window.

Third, three summary statistics are calculated from this exchange rate time series: the minimum
rate observed (the best rate the company experienced), the maximum rate observed (the worst),
and the volatility (maximum minus minimum, divided by minimum, expressed as a percentage).

The volatility figure is the most decision-relevant. A 99.8% volatility figure means that a
company paying USD 10 million for imports at the best rate in the window paid the equivalent
of NGN 8 billion. The same USD 10 million at the worst rate in the window cost NGN 16 billion.
Without any change in supplier pricing, the Naira cost doubled.

**What Decisions This Enables**

FX exposure analysis has several direct applications for finance and procurement leadership.

Budget forecasting: if you know your FX-exposed spend is USD 132 million and the historical
volatility of the exchange rate is 99.8%, you can model the range of possible Naira costs for
next year's budget. Rather than planning on a fixed exchange rate assumption (which will almost
certainly be wrong), you can plan against a range with stated confidence intervals.

Hedging decisions: once the total USD exposure is quantified, the finance team can evaluate
whether currency forward contracts or other hedging instruments are cost-effective. Without
the exposure number, a hedging conversation cannot begin.

Supplier currency renegotiation: in some cases, the procurement team can negotiate to change
the invoicing currency of a contract from USD to NGN, shifting the FX risk onto the supplier.
The exposure analysis identifies which contracts this is most worthwhile for.

Dual-currency sourcing strategy: knowing the total FX exposure allows procurement leadership
to set deliberate targets for domestic versus import sourcing, reducing the FX exposure
structurally rather than managing it financially.

**The Dashboard View**

In the Risk and Uncertainty page of the dashboard, the FX KPIs sit alongside the supply risk
metrics: total USD exposure, FX volatility percentage, and the range of NGN/USD rates observed
in the period.

These three numbers frame the FX risk conversation in about 10 seconds. The CFO or finance
director who sees them immediately understands the scale and direction of the risk without
needing to dig into the underlying data.

The goal is to make the invisible visible. FX exposure in procurement is a real financial risk.
It is also one of the easiest risks to quantify, hedge, or mitigate once someone has measured
it.

---

### X Post (Thread)

**Tweet 1/4**
FX risk is one of the least-discussed cost drivers in procurement.

Not because it's small. Because it's invisible until it's very large.

**Tweet 2/4**
Example: you negotiate a fair USD price with a German supplier.

6 months later, the Naira weakens 30%.

The supplier didn't change anything. You just paid 30% more in Naira.

**Tweet 3/4**
The FX analysis module in my procurement pipeline:
1. Isolates all USD-denominated purchase orders
2. Calculates the min/max exchange rate across the period
3. Computes volatility = (max - min) / min x 100%

Result: $132M exposure, 99.8% FX volatility

**Tweet 4/4**
99.8% volatility means the exchange rate nearly doubled.

The same $10M import order cost NGN 8B at the best rate and NGN 16B at the worst.

You can't hedge what you haven't measured. This analysis is the measurement.

---

---

## POST 8: Planning with Honest Uncertainty

---

### LinkedIn

"You could save NGN 186 billion."

That number is correct. It is also, on its own, almost useless for planning.

A CFO cannot budget against "maybe NGN 186 billion." A board cannot approve a transformation
programme against that number without understanding how confident you are and what the downside
looks like.

What a planning process actually needs is not a single savings estimate. It needs a range, with
stated confidence. Something like: "We are 90% confident savings will fall between NGN 145
billion and NGN 220 billion, with a central estimate of NGN 182 billion."

Producing that range is what scenario analysis and Monte Carlo simulation do.

Scenario analysis applies realistic multipliers to each savings component. The conservative
scenario assumes only 65 to 70% of the theoretical savings are achievable, reflecting contract
constraints, implementation drag, and supplier pushback. The base scenario is the full
identified amount. The aggressive scenario assumes better execution than modelled.

Monte Carlo simulation runs 10,000 versions of the future simultaneously, each with slightly
different assumptions drawn from defined uncertainty bands, and then looks at the distribution
of outcomes. Five percent of scenarios produce savings below the P5 figure. Five percent
produce savings above the P95 figure. The middle 90% of scenarios fall between those two
numbers.

In the procurement analytics pipeline I built:
Conservative scenario: approximately NGN 130 billion.
Aggressive scenario: approximately NGN 223 billion.
Monte Carlo median: aligns closely with the base scenario estimate.
Monte Carlo P5 (pessimistic floor): the threshold only 5 in 100 simulations fell below.
Monte Carlo P95 (optimistic ceiling): the threshold only 5 in 100 simulations exceeded.

The CFO who sees these numbers knows exactly how to build a budget: plan for the central
estimate, build a contingency for the P25 case, and stress-test against the P5 floor.

Honest uncertainty is more useful than false precision. And a confidence range built on
10,000 simulations is much more honest than a single-point estimate that pretends certainty
it does not have.

#Procurement #CostManagement #DataAnalytics #RiskManagement #MonteCarloSimulation

---

### Medium Story

**Title: Planning with Honest Uncertainty: Monte Carlo Simulation in Procurement**
**Subtitle: Why a range is always more useful than a single number when the stakes are high.**

---

Every cost-saving analysis eventually produces a headline number.

In this project, that number is NGN 186 billion. It represents the total identified savings
across three opportunity areas: price standardisation, supplier performance improvement, and
supplier consolidation.

The number is real. The methodology behind it is sound. And it is, on its own, almost useless
for a CFO trying to build next year's budget.

The reason is straightforward. Any headline figure from an analytical model is an estimate.
It is the expected outcome if every recommendation is executed correctly, contracts are
renegotiated as planned, suppliers respond as modelled, and market conditions stay roughly the
same. None of these assumptions will hold perfectly. Some will hold well. Some will not.

The question any planning process needs answered is not "what is the estimate?" but "how much
uncertainty surrounds that estimate, and what does the range of plausible outcomes look like?"

**Scenario Analysis: The Simple Version**

Before introducing Monte Carlo simulation, a simpler tool addresses the same question.

Scenario analysis applies carefully chosen multipliers to each savings component to model
three possible execution outcomes.

The Conservative scenario uses multipliers of 0.70 for price standardisation, 0.65 for
supplier performance improvement, and 0.60 for consolidation. These numbers represent the
kind of shortfall that arises when long-term contracts cannot be renegotiated immediately,
when supplier improvement plans take longer to execute than planned, and when internal
adoption of new procurement policies is partial.

The Base scenario uses multipliers of 1.0 across all components. This is the model's central
estimate, representing the full identified opportunity if execution is well-managed.

The Aggressive scenario uses multipliers above 1.0. This represents the case where
renegotiations out-perform expectations, supplier replacement happens faster than planned, and
additional opportunities surface during implementation.

These three scenarios appear as a simple bar chart in the dashboard. A procurement director
can look at the Conservative bar and ask: "Is this the lowest I should plan for?" and look at
the Aggressive bar and ask: "What would have to go right for us to get here?" Both questions
are strategically useful.

**Monte Carlo Simulation: The Rigorous Version**

Scenario analysis produces three discrete outcomes. Monte Carlo simulation produces a full
probability distribution.

The idea is to run the savings model thousands of times in a row, each time using slightly
different assumptions drawn randomly from defined uncertainty ranges. When all runs are
complete, the distribution of outcomes tells you what the model believes is likely, what it
believes is possible, and what it believes is highly unlikely.

In the procurement analytics pipeline for this project, the simulation runs 10,000 times.

Each run draws a random value for price standardisation savings from a normal distribution
centred on the base estimate with a standard deviation of 15% of that base. Price
standardisation savings are relatively predictable once you know the price variance data,
so 15% uncertainty is a reasonable band.

Each run draws a random value for supplier performance savings with a 20% standard deviation.
This is wider (more uncertain) because the savings from replacing or reforming suppliers depend
on future operational events that are harder to predict.

Each run draws a random value for consolidation savings with a 25% standard deviation. This
is the widest band because consolidation savings are the most speculative of the three: they
depend on volume leverage dynamics that can shift with market conditions.

**Reading the Results**

After 10,000 runs, the results are sorted and presented as percentiles.

The 5th percentile (P5) is the value below which only 5% of simulations fell. This is the
stress-test floor: a number that would only be seen in a genuinely poor execution environment.

The 25th percentile (P25) represents the pessimistic-but-plausible case. One in four simulated
futures produces a result below this number.

The median (50th percentile) is the central tendency of the distribution. In a well-designed
model, the median should align closely with the base scenario estimate.

The 75th percentile (P75) is the optimistic-but-plausible case.

The 95th percentile (P95) is the optimistic ceiling. Only 5% of simulations exceeded this value.

**What Finance Does with These Numbers**

A planning process using these outputs looks like this.

Budget the central estimate (median). This is the most likely outcome, supported by 10,000
simulations, and is the best single number for a budget line.

Build reserves against the P25 case. If actual savings come in at the pessimistic-but-plausible
level, the organisation needs to have a plan for the shortfall.

Stress-test against the P5 floor. The board should see this number. If the organisation can
absorb the savings shortfall at the P5 level without material disruption, the programme is
low-risk to proceed with. If the P5 case would be financially damaging, the risk profile of
the programme needs to be part of the approval decision.

This is planning with honest uncertainty. It is not more pessimistic than single-point
estimation. It is more complete, more defensible, and more useful for the people who have to
act on it.

**The Dashboard**

The Risk and Uncertainty page of the dashboard presents these results in two forms: a set of
metric tiles showing the P5, median, and P95 savings at a glance, and a full Monte Carlo
bounds table showing the complete percentile breakdown.

A CFO who spends 30 seconds on this page leaves with a confident answer to the most important
question any cost-saving programme faces: not "how much could we save?" but "how sure are we,
and what does the downside look like?"

That confidence is the analytical foundation for a programme approval decision.

---

### X Post (Thread)

**Tweet 1/5**
"You could save NGN 186 billion."

Correct. Also almost useless for planning on its own.

A CFO can't budget against "maybe NGN 186B." Here's how you build the honest version.

**Tweet 2/5**
Step 1: Scenario analysis.

Apply realistic multipliers to each savings component:
- Conservative: 65-70% of identified savings (contracts, implementation drag)
- Base: 100% (full model estimate)
- Aggressive: 115-125% (better execution than modelled)

**Tweet 3/5**
Step 2: Monte Carlo simulation.

Run the model 10,000 times, each with randomised assumptions within defined uncertainty bands.

Price savings: +-15% uncertainty
Performance savings: +-20% uncertainty
Consolidation savings: +-25% uncertainty

**Tweet 4/5**
The output is a probability distribution:

P5 = only 5% of simulations produced less than this (the stress-test floor)
Median = 50% above, 50% below (best single estimate)
P95 = only 5% of simulations exceeded this (the optimistic ceiling)

**Tweet 5/5**
How finance uses this:
- Budget the median
- Build reserves against P25
- Stress-test board approval against P5

Honest uncertainty is more useful than false precision.
10,000 simulations give you the range to plan against.
