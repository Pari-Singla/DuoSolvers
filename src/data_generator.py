# src/data_generator.py
import pandas as pd
import numpy as np
import sqlite3
import os

def generate_and_load_sqlite(db_path="data/kpi.db"):
    """Generates 6 months of orders, marketing, targets. Includes Product C with sparse history."""
    
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    dates = pd.date_range('2026-01-01', '2026-06-30', freq='D')
    regions = ['North', 'South', 'East']
    products_full = ['A', 'B']  # Full history for A and B
    products_sparse = ['C']     # Sparse history for C (only last 7 days)
    
    np.random.seed(42)
    orders_data = []

    # Generate for A and B (full 6 months)
    for d in dates:
        for r in regions:
            for p in products_full:
                units = np.random.randint(50, 200)
                price = round(np.random.uniform(10, 30), 2)
                orders_data.append([d.strftime('%Y-%m-%d'), r, p, units, price])

    # Generate for C (sparse: only June 24 - June 30 to simulate <14 days history)
    sparse_dates = pd.date_range('2026-06-24', '2026-06-30', freq='D')
    for d in sparse_dates:
        for r in regions:
            units = np.random.randint(50, 150)
            price = round(np.random.uniform(10, 25), 2)
            orders_data.append([d.strftime('%Y-%m-%d'), r, 'C', units, price])

    df_orders = pd.DataFrame(orders_data, columns=['date', 'region', 'product_line', 'units_sold', 'avg_price'])
    df_orders['revenue'] = df_orders['units_sold'] * df_orders['avg_price']
    
    # --- INJECT ANOMALY (East, Product A, June 1-15, Units drop 40%) ---
    mask = (df_orders['date'] >= '2026-06-01') & (df_orders['date'] <= '2026-06-15')
    mask &= (df_orders['region'] == 'East') & (df_orders['product_line'] == 'A')
    df_orders.loc[mask, 'units_sold'] = (df_orders.loc[mask, 'units_sold'] * 0.6).astype(int)
    df_orders.loc[mask, 'revenue'] = df_orders.loc[mask, 'units_sold'] * df_orders.loc[mask, 'avg_price']
    
    # Marketing
    channels = ['social', 'search', 'display']
    mkt_data = []
    for d in dates:
        for r in regions:
            for ch in channels:
                spend = np.random.randint(100, 500)
                mkt_data.append([d.strftime('%Y-%m-%d'), r, ch, spend])
    df_mkt = pd.DataFrame(mkt_data, columns=['date', 'region', 'channel', 'spend'])
    
    # Targets
    months = pd.date_range('2026-01-01', '2026-06-30', freq='M')
    target_data = []
    for m in months:
        for r in regions:
            target = np.random.randint(100000, 200000)
            target_data.append([m.strftime('%Y-%m-%d'), r, target])
    df_targets = pd.DataFrame(target_data, columns=['month', 'region', 'revenue_target'])
    
    conn = sqlite3.connect(db_path)
    df_orders.to_sql('orders', conn, if_exists='replace', index=False)
    df_mkt.to_sql('marketing_spend', conn, if_exists='replace', index=False)
    df_targets.to_sql('targets', conn, if_exists='replace', index=False)
    conn.close()
    
    print(f"✅ Data generated and loaded into {db_path}")
    print(f"   - Orders: {len(df_orders)} rows")
    print(f"   - Marketing: {len(df_mkt)} rows")
    print(f"   - Targets: {len(df_targets)} rows")
    print("   - Anomaly injected: East/Product A, June 1-15 (units dropped 40%)")
    print("   - Sparse history: Product C generated only for June 24-30 (<14 days)")

if __name__ == "__main__":
    generate_and_load_sqlite()