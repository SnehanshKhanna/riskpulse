from typing import Dict, Any

class ValuationEngine:
    def __init__(self):
        pass
        
    def calculate_delta(self, position: Dict[str, Any], shock: Dict[str, Any]) -> Dict[str, Any]:
        """
        position: dict representing PortfolioPosition
        shock: dict with keys like `equity_shock_pct`, `rate_shift_bp`, `credit_spread_bp`, `pd_multiplier`, `fx_usd_shock_pct`
        """
        asset_class = position.get("asset_class")
        instrument_type = position.get("instrument_type")
        current_value = position.get("current_value", 0.0)
        notional = position.get("notional", 0.0)
        ead = position.get("exposure", current_value)
        
        loss_breakdown = {
            "rate": 0.0,
            "spread": 0.0,
            "equity": 0.0,
            "credit_loss": 0.0,
            "fx": 0.0,
            "vol": 0.0
        }
        
        # Shocks
        rate_shift_bp = shock.get("rate_shift_bp", 0.0)
        spread_bp = shock.get("credit_spread_bp", 0.0)
        eq_shock = shock.get("equity_shock_pct", 0.0)
        pd_mult = shock.get("pd_multiplier", 1.0)
        fx_shock = shock.get("fx_usd_shock_pct", 0.0)
        
        # 1. Interest Rate & Spread (Bonds, Fixed Loans)
        if asset_class in ["Corporate Bond", "Government Bond", "Corporate Loan"] and instrument_type != "Floating":
            mod_dur = position.get("modified_duration", 0.0)
            conv = position.get("convexity", 0.0)
            spread_dur = position.get("spread_duration", 0.0)
            
            rate_delta = -mod_dur * current_value * (rate_shift_bp / 10000.0) + 0.5 * conv * current_value * ((rate_shift_bp / 10000.0) ** 2)
            loss_breakdown["rate"] = rate_delta
            
            if asset_class == "Corporate Bond" or asset_class == "Corporate Loan":
                spread_delta = -spread_dur * current_value * (spread_bp / 10000.0)
                loss_breakdown["spread"] = spread_delta

        # 2. Credit Loss (Loans, Bonds) - Expected Loss shift
        if asset_class in ["Corporate Loan", "Corporate Bond"]:
            pd_base = position.get("pd_base", 0.01)
            lgd = position.get("lgd", 0.45)
            pd_stressed = min(1.0, pd_base * pd_mult)
            
            # EL = EAD * PD * LGD. We book the INCREASE in EL as a loss.
            el_base = ead * pd_base * lgd
            el_stressed = ead * pd_stressed * lgd
            loss_breakdown["credit_loss"] = -(el_stressed - el_base)
            
        # 3. Equities
        if asset_class == "Equity":
            beta = position.get("beta", 1.0)
            loss_breakdown["equity"] = current_value * beta * eq_shock
            
        # 4. IR Swaps
        if asset_class == "Derivative" and instrument_type == "IR Swap":
            dv01 = position.get("dv01", 0.0)
            # dv01 is value change per 1bp. If pay fixed, dv01 is positive for rate increase.
            loss_breakdown["rate"] = dv01 * rate_shift_bp
            
        # 5. CDS
        if asset_class == "Derivative" and instrument_type == "CDS":
            spread_dur = position.get("spread_duration", 0.0)
            # Protection buyer: gains if spread widens
            loss_breakdown["spread"] = spread_dur * notional * (spread_bp / 10000.0)
            
        # 6. FX Forwards
        if asset_class == "Derivative" and instrument_type == "FX Forward":
            delta = position.get("delta", 0.0)
            loss_breakdown["fx"] = notional * delta * fx_shock
            
        total_delta = sum(loss_breakdown.values())
        value_after = current_value + total_delta
        
        return {
            "value_before": current_value,
            "value_after": value_after,
            "loss": -total_delta,
            "driver_breakdown": loss_breakdown
        }
