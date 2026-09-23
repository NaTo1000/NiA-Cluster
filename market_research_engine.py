#!/usr/bin/env python3
"""Market research and compliance patterning engine."""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Any


class MarketResearchEngine:
    """Builds layered market patterns from public records and compliance signals."""

    def __init__(self, vm_layers: int = 3):
        self.vm_layers = max(1, vm_layers)

    def run(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        normalized = [self._normalize_record(record) for record in records]
        multiplexed = self._multiplex_by_company(normalized)
        patterns = self._build_patterns(multiplexed)
        compliance = self._compliance_summary(normalized)
        return {
            "vm_layers": self.vm_layers,
            "input_records": len(records),
            "multiplexed_companies": len(multiplexed),
            "patterns": patterns,
            "compliance": compliance,
        }

    def _normalize_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        normalized = dict(record)
        normalized["company"] = (record.get("company") or "unknown").strip().lower()
        normalized["source_public"] = bool(record.get("source_public", False))
        normalized["company_sales"] = float(record.get("company_sales", 0.0))
        normalized["future_investment"] = float(record.get("future_investment", 0.0))
        normalized["merger_opportunity"] = float(record.get("merger_opportunity", 0.0))
        normalized["tax_regulation_score"] = float(record.get("tax_regulation_score", 0.0))
        normalized["financing_regulation_score"] = float(record.get("financing_regulation_score", 0.0))
        return normalized

    def _multiplex_by_company(self, records: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for record in records:
            grouped[record["company"]].append(record)

        multiplexed: Dict[str, Dict[str, Any]] = {}
        for company, company_records in grouped.items():
            public_records = [record for record in company_records if record["source_public"]]
            sales = sum(record["company_sales"] for record in public_records)
            investment = sum(record["future_investment"] for record in public_records)
            merger = sum(record["merger_opportunity"] for record in public_records)
            tax = sum(record["tax_regulation_score"] for record in public_records)
            financing = sum(record["financing_regulation_score"] for record in public_records)

            record_count = len(public_records)
            if record_count:
                tax /= record_count
                financing /= record_count

            multiplexed[company] = {
                "public_records": record_count,
                "sales_signal": sales,
                "investment_signal": investment,
                "merger_signal": merger,
                "tax_compliance_signal": tax,
                "financing_compliance_signal": financing,
            }
        return multiplexed

    def _build_patterns(self, multiplexed: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        patterns: List[Dict[str, Any]] = []
        for company, signals in multiplexed.items():
            if signals["public_records"] == 0:
                continue

            growth = signals["sales_signal"] + signals["investment_signal"]
            strategic = growth + signals["merger_signal"]
            layered_score = strategic
            for layer_index in range(1, self.vm_layers):
                reinforcement = strategic * (1 + (0.05 * layer_index))
                layered_score = (layered_score * 0.75) + (reinforcement * 0.25)

            pattern_type = "watch"
            if layered_score >= 150:
                pattern_type = "high-opportunity"
            elif layered_score >= 80:
                pattern_type = "growth"

            patterns.append(
                {
                    "company": company,
                    "pattern_type": pattern_type,
                    "layered_score": round(layered_score, 2),
                    "tax_compliance_signal": round(signals["tax_compliance_signal"], 2),
                    "financing_compliance_signal": round(signals["financing_compliance_signal"], 2),
                }
            )
        return sorted(patterns, key=lambda p: p["layered_score"], reverse=True)

    def _compliance_summary(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        total = len(records)
        public_records = sum(1 for record in records if record["source_public"])
        compliant_records = sum(
            1
            for record in records
            if record["source_public"]
            and record["tax_regulation_score"] >= 0.5
            and record["financing_regulation_score"] >= 0.5
        )
        return {
            "total_records": total,
            "public_records": public_records,
            "compliant_public_records": compliant_records,
            "non_public_records_excluded": total - public_records,
        }
