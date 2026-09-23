#!/usr/bin/env python3
"""Market research and compliance patterning engine."""
from __future__ import annotations

from collections import defaultdict
import math
from typing import Dict, List, Any


class MarketResearchInputError(ValueError):
    """Raised when research input records contain invalid types/values."""


class MarketResearchEngine:
    """Builds layered market patterns from public records and compliance signals."""

    def __init__(self, vm_layers: int = 3):
        if not isinstance(vm_layers, int) or isinstance(vm_layers, bool):
            raise MarketResearchInputError("vm_layers must be an integer")
        if vm_layers <= 0:
            raise MarketResearchInputError("vm_layers must be a positive integer")
        self.vm_layers = vm_layers

    def run(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        normalized = [self._normalize_record(record, index) for index, record in enumerate(records)]
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

    def _normalize_record(self, record: Dict[str, Any], index: int) -> Dict[str, Any]:
        if not isinstance(record, dict):
            raise MarketResearchInputError(f"record {index} must be an object")

        company = record.get("company")
        if not isinstance(company, str) or not company.strip():
            raise MarketResearchInputError(f"record {index} has invalid company; expected string value")

        normalized = dict(record)
        normalized["company"] = company.strip().lower()
        normalized["source_public"] = self._parse_bool(record.get("source_public", False), "source_public", index)
        normalized["company_sales"] = self._parse_float(record.get("company_sales", 0.0), "company_sales", index)
        normalized["future_investment"] = self._parse_float(record.get("future_investment", 0.0), "future_investment", index)
        normalized["merger_opportunity"] = self._parse_float(record.get("merger_opportunity", 0.0), "merger_opportunity", index)
        normalized["tax_regulation_score"] = self._parse_float(record.get("tax_regulation_score", 0.0), "tax_regulation_score", index)
        normalized["financing_regulation_score"] = self._parse_float(record.get("financing_regulation_score", 0.0), "financing_regulation_score", index)
        return normalized

    def _parse_bool(self, value: Any, field_name: str, index: int) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"true", "1", "yes"}:
                return True
            if lowered in {"false", "0", "no"}:
                return False
        raise MarketResearchInputError(f"record {index} has invalid {field_name}; expected boolean-like value")

    def _parse_float(self, value: Any, field_name: str, index: int) -> float:
        if isinstance(value, bool):
            raise MarketResearchInputError(f"record {index} has invalid {field_name}; expected numeric value")
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            raise MarketResearchInputError(f"record {index} has invalid {field_name}; expected numeric value")
        if not math.isfinite(parsed):
            raise MarketResearchInputError(f"record {index} has invalid {field_name}; expected finite numeric value")
        return parsed

    def _multiplex_by_company(self, records: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for record in records:
            grouped[record["company"]].append(record)

        multiplexed: Dict[str, Dict[str, Any]] = {}
        for company, company_records in grouped.items():
            sales = 0.0
            investment = 0.0
            merger = 0.0
            tax = 0.0
            financing = 0.0
            record_count = 0
            for record in company_records:
                if not record["source_public"]:
                    continue
                record_count += 1
                sales += record["company_sales"]
                investment += record["future_investment"]
                merger += record["merger_opportunity"]
                tax += record["tax_regulation_score"]
                financing += record["financing_regulation_score"]

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
