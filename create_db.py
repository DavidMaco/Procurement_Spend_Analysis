"""
Load procurement data into SQLite database
Simpler alternative for portfolio project
"""

import pandas as pd
import sqlite3
import os

def create_database():
    """Create SQLite database and load data"""
    
    db_path = 'procurement.db'
    
    # Remove existing database
    if os.path.exists(db_path):
        os.remove(db_path)
    
    # Create connection
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("CREATING PROCUREMENT DATABASE")
    print("=" * 60)
    
    # Load CSV files
    print("\nLoading data files...")
    
    suppliers_df = pd.read_csv('suppliers.csv')
    materials_df = pd.read_csv('materials.csv')
    pos_df = pd.read_csv('purchase_orders.csv')
    incidents_df = pd.read_csv('quality_incidents.csv')
    
    # Write to database
    print(f"  Loading {len(suppliers_df)} suppliers...")
    suppliers_df.to_sql('suppliers', conn, if_exists='replace', index=False)
    
    print(f"  Loading {len(materials_df)} materials...")
    materials_df.to_sql('materials', conn, if_exists='replace', index=False)
    
    print(f"  Loading {len(pos_df)} purchase orders...")
    pos_df.to_sql('purchase_orders', conn, if_exists='replace', index=False)
    
    print(f"  Loading {len(incidents_df)} quality incidents...")
    incidents_df.to_sql('quality_incidents', conn, if_exists='replace', index=False)
    
    # Create indexes
    print("\nCreating indexes...")
    cursor.execute('CREATE INDEX idx_po_date ON purchase_orders(po_date)')
    cursor.execute('CREATE INDEX idx_po_supplier ON purchase_orders(supplier_id)')
    cursor.execute('CREATE INDEX idx_po_category ON purchase_orders(category)')
    
    # Create views
    print("Creating analytical views...")
    
    # Supplier Performance View
    cursor.execute('''
        CREATE VIEW vw_supplier_performance AS
        SELECT 
            s.supplier_id,
            s.supplier_name,
            s.category,
            s.country,
            s.risk_level,
            s.quality_rating,
            COUNT(DISTINCT po.po_number) as total_orders,
            ROUND(SUM(po.total_amount_ngn), 2) as total_spend_ngn,
            ROUND(AVG(po.total_amount_ngn), 2) as avg_order_value,
            ROUND(
                SUM(CASE WHEN po.actual_delivery_date <= po.expected_delivery_date THEN 1 ELSE 0 END) * 100.0 / 
                NULLIF(COUNT(CASE WHEN po.actual_delivery_date IS NOT NULL THEN 1 END), 0),
                2
            ) as on_time_delivery_pct,
            COUNT(DISTINCT qi.incident_id) as quality_incidents,
            ROUND(COALESCE(SUM(qi.cost_impact_ngn), 0), 2) as total_quality_cost
        FROM suppliers s
        LEFT JOIN purchase_orders po ON s.supplier_id = po.supplier_id
        LEFT JOIN quality_incidents qi ON s.supplier_id = qi.supplier_id
        GROUP BY s.supplier_id, s.supplier_name, s.category, s.country, s.risk_level, s.quality_rating
    ''')
    
    # Category Spend View
    cursor.execute('''
        CREATE VIEW vw_category_spend AS
        SELECT 
            category,
            strftime('%Y', po_date) as year,
            strftime('%m', po_date) as month,
            COUNT(DISTINCT po_number) as total_orders,
            ROUND(SUM(total_amount_ngn), 2) as total_spend_ngn,
            ROUND(AVG(total_amount_ngn), 2) as avg_order_value,
            COUNT(DISTINCT supplier_id) as unique_suppliers
        FROM purchase_orders
        WHERE po_date IS NOT NULL
        GROUP BY category, year, month
    ''')
    
    # Savings Opportunities View
    cursor.execute('''
        CREATE VIEW vw_savings_opportunities AS
        SELECT 
            category,
            supplier_name,
            COUNT(*) as order_count,
            ROUND(AVG(unit_price_ngn), 2) as avg_price_paid,
            ROUND(MIN(unit_price_ngn), 2) as best_price,
            ROUND((AVG(unit_price_ngn) - MIN(unit_price_ngn)) / MIN(unit_price_ngn) * 100, 2) as potential_savings_pct,
            ROUND(SUM(total_amount_ngn) * (AVG(unit_price_ngn) - MIN(unit_price_ngn)) / AVG(unit_price_ngn), 0) as potential_savings_ngn
        FROM purchase_orders
        GROUP BY category, supplier_name
        HAVING COUNT(*) > 5 AND potential_savings_pct > 5
    ''')
    
    conn.commit()
    
    # Verify data
    print("\n" + "=" * 60)
    print("DATABASE VERIFICATION")
    print("=" * 60)
    
    result = cursor.execute("SELECT COUNT(*) FROM suppliers").fetchone()
    print(f"\nTotal Suppliers: {result[0]}")
    
    result = cursor.execute("SELECT COUNT(*) FROM materials").fetchone()
    print(f"Total Materials: {result[0]}")
    
    result = cursor.execute("SELECT COUNT(*) FROM purchase_orders").fetchone()
    print(f"Total Purchase Orders: {result[0]}")
    
    result = cursor.execute("SELECT ROUND(SUM(total_amount_ngn), 0) FROM purchase_orders").fetchone()
    print(f"Total Procurement Spend: ₦{result[0]:,.0f}")
    
    result = cursor.execute('''
        SELECT category, ROUND(SUM(total_amount_ngn), 0) as spend 
        FROM purchase_orders 
        GROUP BY category 
        ORDER BY spend DESC 
        LIMIT 3
    ''').fetchall()
    
    print("\nTop 3 Categories by Spend:")
    for cat, spend in result:
        print(f"  {cat}: ₦{spend:,.0f}")
    
    result = cursor.execute('''
        SELECT COUNT(*) as late_deliveries,
               ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM purchase_orders WHERE actual_delivery_date IS NOT NULL), 2) as pct
        FROM purchase_orders 
        WHERE actual_delivery_date > expected_delivery_date
    ''').fetchone()
    
    print(f"\nLate Deliveries: {result[0]} ({result[1]}%)")
    
    result = cursor.execute("SELECT COUNT(*) FROM quality_incidents").fetchone()
    print(f"Quality Incidents: {result[0]}")
    
    result = cursor.execute("SELECT ROUND(SUM(cost_impact_ngn), 0) FROM quality_incidents").fetchone()
    print(f"Quality Cost Impact: ₦{result[0]:,.0f}")
    
    print("\n" + "=" * 60)
    print("✓ DATABASE CREATED SUCCESSFULLY!")
    print("=" * 60)
    print(f"\nDatabase file: {os.path.abspath(db_path)}")
    print("\nYou can now query the database using:")
    print("  - Python (sqlite3 or pandas)")
    print("  - SQL tools (DB Browser for SQLite, DBeaver)")
    print("  - Power BI (ODBC connector)")
    
    conn.close()
    
    return db_path

if __name__ == "__main__":
    create_database()
