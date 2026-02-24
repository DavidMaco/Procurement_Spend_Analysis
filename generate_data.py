"""
FMCG Procurement Data Generator
Generates realistic procurement data for portfolio project
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

np.random.seed(42)
random.seed(42)

def generate_suppliers():
    """Generate supplier master data"""
    supplier_categories = {
        'Raw Materials': ['Sugar', 'Flour', 'Milk Powder', 'Cocoa', 'Palm Oil'],
        'Packaging': ['Bottles', 'Cartons', 'Labels', 'Caps'],
        'Equipment': ['Processing Equipment', 'Packaging Machines'],
        'Services': ['Maintenance', 'Logistics', 'Quality Testing']
    }
    
    countries = {'Nigeria': 0.35, 'India': 0.20, 'China': 0.18, 'Germany': 0.10, 'USA': 0.08, 'UK': 0.09}
    
    suppliers = []
    supplier_id = 1000
    
    for category, subcats in supplier_categories.items():
        for i in range(random.randint(8, 12)):
            country = np.random.choice(list(countries.keys()), p=list(countries.values()))
            suppliers.append({
                'supplier_id': f'SUP{supplier_id}',
                'supplier_name': f'{category} Supplier {i+1} ({country[:3].upper()})',
                'category': category,
                'country': country,
                'payment_terms': random.choice(['Net 30', 'Net 45', 'Net 60']),
                'currency': 'NGN' if country == 'Nigeria' else 'USD',
                'quality_rating': round(random.uniform(3.0, 5.0), 2),
                'is_approved': random.random() > 0.25,
                'risk_level': random.choice(['Low', 'Low', 'Medium', 'High'])
            })
            supplier_id += 1
    return pd.DataFrame(suppliers)

def generate_materials():
    """Generate materials master"""
    materials = []
    mat_id = 2000
    categories = ['Raw Materials', 'Packaging', 'Equipment', 'Services']
    
    for cat in categories:
        for i in range(random.randint(15, 25)):
            materials.append({
                'material_id': f'MAT{mat_id}',
                'material_name': f'{cat} Item {i+1}',
                'category': cat,
                'unit_of_measure': random.choice(['KG', 'MT', 'LTR', 'PCS']),
                'standard_price_ngn': round(random.uniform(500, 500000), 2),
                'lead_time_days': random.randint(7, 90)
            })
            mat_id += 1
    return pd.DataFrame(materials)

def generate_purchase_orders(suppliers_df, materials_df, num_orders=2500):
    """Generate PO transactions"""
    start_date = datetime.now() - timedelta(days=730)
    orders = []
    po_id = 100000
    
    for _ in range(num_orders):
        po_date = start_date + timedelta(days=random.randint(0, 730))
        category = random.choice(suppliers_df['category'].unique())
        
        supplier = suppliers_df[(suppliers_df['category'] == category) & (suppliers_df['is_approved'])].sample(1).iloc[0]
        material = materials_df[materials_df['category'] == category].sample(1).iloc[0]
        
        quantity = random.randint(10, 1000)
        unit_price = material['standard_price_ngn'] * random.uniform(0.85, 1.25)
        
        if supplier['currency'] == 'USD':
            exchange_rate = random.uniform(800, 1600)
            total_usd = (unit_price / exchange_rate) * quantity
            total_ngn = total_usd * exchange_rate
        else:
            exchange_rate = 1
            total_ngn = unit_price * quantity
            total_usd = None
        
        expected_delivery = po_date + timedelta(days=int(material['lead_time_days']))
        actual_delivery = expected_delivery + timedelta(days=random.randint(-5, 30)) if random.random() > 0.3 else expected_delivery
        
        if actual_delivery > datetime.now():
            actual_delivery, delivery_status, payment_status = None, 'Pending', 'Pending'
        else:
            delivery_status = 'Delivered' if random.random() > 0.05 else 'Partial'
            payment_status = random.choice(['Paid', 'Paid', 'Pending', 'Overdue'])
        
        orders.append({
            'po_number': f'PO{po_id}',
            'po_date': po_date.date(),
            'supplier_id': supplier['supplier_id'],
            'supplier_name': supplier['supplier_name'],
            'material_id': material['material_id'],
            'material_name': material['material_name'],
            'category': category,
            'quantity': quantity,
            'unit_price_ngn': round(unit_price, 2),
            'total_amount_ngn': round(total_ngn, 2),
            'total_amount_usd': round(total_usd, 2) if total_usd else None,
            'currency': supplier['currency'],
            'expected_delivery_date': expected_delivery.date(),
            'actual_delivery_date': actual_delivery.date() if actual_delivery else None,
            'delivery_status': delivery_status,
            'payment_status': payment_status,
            'buyer': random.choice(['John Obi', 'Sarah Ahmed', 'Chidi Eze']),
            'plant_location': random.choice(['Lagos', 'Ibadan', 'Kano'])
        })
        po_id += 1
    return pd.DataFrame(orders)

def generate_quality_incidents(pos_df, num=150):
    """Generate quality incidents"""
    delivered = pos_df[pos_df['delivery_status'] == 'Delivered'].sample(n=min(num, len(pos_df)))
    incidents = []
    for idx, (i, po) in enumerate(delivered.iterrows()):
        incidents.append({
            'incident_id': f'QI{5000 + idx}',
            'po_number': po['po_number'],
            'supplier_id': po['supplier_id'],
            'incident_type': random.choice(['Quality Defect', 'Contamination', 'Wrong Spec']),
            'severity': random.choice(['Low', 'Medium', 'High']),
            'cost_impact_ngn': round(random.uniform(50000, po['total_amount_ngn'] * 0.3), 2)
        })
    return pd.DataFrame(incidents)

if __name__ == "__main__":
    print("Generating data...")
    suppliers_df = generate_suppliers()
    materials_df = generate_materials()
    pos_df = generate_purchase_orders(suppliers_df, materials_df, 2500)
    incidents_df = generate_quality_incidents(pos_df)
    
    suppliers_df.to_csv('suppliers.csv', index=False)
    materials_df.to_csv('materials.csv', index=False)
    pos_df.to_csv('purchase_orders.csv', index=False)
    incidents_df.to_csv('quality_incidents.csv', index=False)
    
    print(f"\n✓ Generated:")
    print(f"  {len(suppliers_df)} suppliers")
    print(f"  {len(materials_df)} materials")
    print(f"  {len(pos_df)} purchase orders")
    print(f"  {len(incidents_df)} quality incidents")
    print(f"\nTotal Spend: ₦{pos_df['total_amount_ngn'].sum():,.0f}")
