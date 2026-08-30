# src/config.py

KPI_CONTRACTS = {
    "revenue": {
        "calculation": "SUM(units_sold * avg_price)",
        "dimensions": ["region", "product_line"],
        "refresh": "daily",
        "source_table": "orders",
        "owner": "finance",
        "security_roles": {
            "manager": ["region"],
            "analyst": ["region", "product_line"],
            "executive": []
        },
        "decomposition": ["units_sold", "avg_price"],
        "min_history_days": 14
    },
    "units_sold": {
        "calculation": "SUM(units_sold)",
        "dimensions": ["region", "product_line"],
        "refresh": "daily",
        "source_table": "orders",
        "owner": "operations",
        "security_roles": {
            "manager": ["region"],
            "analyst": ["region", "product_line"],
            "executive": []
        },
        "decomposition": [],
        "min_history_days": 14
    },
    "avg_price": {
        "calculation": "AVG(avg_price)",
        "dimensions": ["region", "product_line"],
        "refresh": "daily",
        "source_table": "orders",
        "owner": "pricing",
        "security_roles": {
            "manager": ["region"],
            "analyst": ["region", "product_line"],
            "executive": []
        },
        "decomposition": [],
        "min_history_days": 14
    }
}

ROLE_LEVELS = {
    "manager": {"region": "East"},
    "analyst": {},
    "executive": {}
}

ACTION_RULES = [
    {"condition": "volume_drop", "action": "Increase marketing spend in the affected region", "owner": "Marketing", "levers": ["ad spend", "promotions"]},
    {"condition": "price_drop", "action": "Review pricing strategy and consider bundling", "owner": "Pricing", "levers": ["discounts", "bundles"]},
    {"condition": "mix_shift", "action": "Realign product mix to favor high-margin items", "owner": "Product", "levers": ["inventory", "merchandising"]},
    {"condition": "external", "action": "Investigate competitor activity and market trends", "owner": "Strategy", "levers": ["competitive intel", "surveys"]}
]