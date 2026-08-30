# src/telemetry.py
import time

class TelemetryLogger:
    def __init__(self):
        self.requests = []
    
    def log_request(self, endpoint, latency_ms, llm_calls=0, tokens=0, cost=0.0):
        self.requests.append({
            "endpoint": endpoint,
            "timestamp": time.time(),
            "latency_ms": latency_ms,
            "llm_calls": llm_calls,
            "tokens": tokens,
            "cost": cost
        })
    
    def get_summary(self):
        total = len(self.requests)
        if total == 0:
            return {
                "total_requests": 0,
                "avg_latency_ms": 0,
                "total_llm_calls": 0,
                "total_tokens": 0,
                "estimated_cost_usd": 0.0
            }
        return {
            "total_requests": total,
            "avg_latency_ms": round(sum(r['latency_ms'] for r in self.requests) / total, 2),
            "total_llm_calls": sum(r['llm_calls'] for r in self.requests),
            "total_tokens": sum(r['tokens'] for r in self.requests),
            "estimated_cost_usd": round(sum(r['cost'] for r in self.requests), 4)
        }