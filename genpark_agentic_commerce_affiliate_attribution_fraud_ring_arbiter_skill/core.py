# -*- coding: utf-8 -*-
"""Affiliate Attribution & Fraud Ring Arbiter Skill for GenPark Agentic Commerce."""
import json
from typing import Dict, Any, List

def audit_affiliate_conversion_integrity(affiliate_id: str, order_id: str, order_value_usd: float, click_to_conversion_seconds: int, has_organic_cart_prior_to_click: bool, http_referrer: str = "") -> Dict[str, Any]:
    fraud_score = 0.0
    flags = []

    # Cookie stuffing indicator: click occurred less than 4 seconds before checkout completion
    if click_to_conversion_seconds < 4:
        fraud_score += 65.0
        flags.append("Instantaneous conversion latency (<4s) strongly indicates programmatic cookie stuffing or checkout extension hijacking.")

    # Coupon poaching indicator: Cart already populated organically before affiliate click
    if has_organic_cart_prior_to_click:
        fraud_score += 35.0
        flags.append("Last-second checkout attribution poach: user had pre-existing active shopping cart.")

    # Check referrer domain for suspicious ad-ware or zero-click redirects
    if not http_referrer or "toolbar" in http_referrer.lower() or "extension" in http_referrer.lower():
        fraud_score += 20.0
        flags.append("Suspicious browser extension or empty referrer header detected.")

    final_fraud_score = min(100.0, fraud_score)
    is_fraudulent = final_fraud_score >= 50.0

    standard_commission_usd = round(order_value_usd * 0.08, 2)
    payout_approved = not is_fraudulent

    return {
        "affiliate_id": affiliate_id,
        "order_id": order_id,
        "order_value_usd": order_value_usd,
        "fraud_risk_score": final_fraud_score,
        "attribution_status": "REJECTED_CLAWBACK" if is_fraudulent else "APPROVED_VERIFIED",
        "eligible_commission_payout_usd": standard_commission_usd if payout_approved else 0.0,
        "detected_infractions": flags,
        "compliance_action": "Freeze affiliate account and claw back pending commission." if is_fraudulent else "Release scheduled batch payout.",
        "arbiter": "GenPark Commerce Integrity Shield"
    }

def calculate_multi_touch_payout_split(gross_commission_pool_usd: float, touchpoints: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not touchpoints:
        return {"error": "touchpoints list cannot be empty"}

    n = len(touchpoints)
    splits = []

    # Position-based (U-shaped) attribution: 40% First, 40% Last, 20% Middle shared
    if n == 1:
        weights = [1.0]
    elif n == 2:
        weights = [0.5, 0.5]
    else:
        middle_weight = 0.20 / (n - 2)
        weights = [0.40] + [middle_weight] * (n - 2) + [0.40]

    for idx, tp in enumerate(touchpoints):
        channel = tp.get("channel_type")
        weight = weights[idx]
        
        # Penalize low-value coupon aggregators on last-touch
        if channel == "coupon_aggregator" and idx == (n - 1):
            penalty_factor = 0.5
            adjusted_weight = weight * penalty_factor
        else:
            adjusted_weight = weight

        allocated_usd = round(gross_commission_pool_usd * adjusted_weight, 2)
        splits.append({
            "affiliate_id": tp.get("affiliate_id"),
            "channel_type": channel,
            "touch_position": idx + 1,
            "attribution_share_pct": round(adjusted_weight * 100, 1),
            "allocated_commission_usd": allocated_usd
        })

    return {
        "gross_pool_usd": gross_commission_pool_usd,
        "touchpoints_count": n,
        "attribution_model": "Position-Based U-Shaped with Coupon Discount Deprecation",
        "allocations": splits
    }
