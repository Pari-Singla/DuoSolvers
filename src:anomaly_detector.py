# src/anomaly_detector.py
import pandas as pd
import numpy as np
import sqlite3

class AnomalyDetector:
    def __init__(self, db_path="data/kpi.db"):
        self.db_path = db_path
        
    def _fetch_kpi(self, kpi_name, dimension_filters=None):
        from config import KPI_CONTRACTS
        contract = KPI_CONTRACTS.get(kpi_name)
        if not contract:
            raise ValueError(f"KPI {kpi_name} not in contracts.")
        
        sql = f"SELECT date, {contract['calculation']} as value FROM {contract['source_table']}"
        if dimension_filters:
            filters = " AND ".join([f"{k} = '{v}'" for k, v in dimension_filters.items()])
            sql += f" WHERE {filters}"
        sql += " GROUP BY date ORDER BY date"
        
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query(sql, conn)
        conn.close()
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date').sort_index()
        return df['value']
    
    def detect_anomalies(self, kpi_name, dimension_filters=None, window=28, threshold=2.5):
        series = self._fetch_kpi(kpi_name, dimension_filters)
        if len(series) < window:
            return []  # Not enough history
        
        rolling_mean = series.rolling(window=window, min_periods=1).mean()
        rolling_std = series.rolling(window=window, min_periods=1).std().replace(0, np.nan)
        zscore = (series - rolling_mean) / rolling_std
        
        anomalies = []
        for idx, val in zscore.items():
            if pd.isna(val):
                continue
            if abs(val) > threshold:
                impact = series.loc[idx] - rolling_mean.loc[idx]
                confidence = float(1 - 1/(1 + np.exp(-abs(val))))
                anomalies.append({
                    "kpi": kpi_name,
                    "dimensions": dimension_filters or {},
                    "date": idx.strftime('%Y-%m-%d'),
                    "current_value": float(series.loc[idx]),
                    "expected_value": float(rolling_mean.loc[idx]),
                    "deviation_percent": float((series.loc[idx] - rolling_mean.loc[idx]) / rolling_mean.loc[idx] * 100),
                    "impact": float(impact),
                    "zscore": float(val),
                    "confidence": round(confidence, 3)
                })
        anomalies.sort(key=lambda x: abs(x['zscore']), reverse=True)
        return anomalies