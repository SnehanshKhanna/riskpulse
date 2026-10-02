import yaml
import json
import uuid
from typing import Dict, Any, List
from src.stress_engine.valuation import ValuationEngine
from src.risk_engine.schemas import RiskSignalSchema
from sqlalchemy.orm import Session
from src.db.models import PortfolioPosition, StressRun, StressPositionResult

class StressEngine:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.valuation_engine = ValuationEngine()
        
        with open("data/config/scenarios.yaml", "r") as f:
            self.scenarios = yaml.safe_load(f)
            
        with open("data/config/trigger_rules.yaml", "r") as f:
            self.trigger_rules = yaml.safe_load(f).get("rules", [])
            
    def check_trigger(self, signal: RiskSignalSchema) -> str:
        for rule in self.trigger_rules:
            cond = rule["conditions"]
            if signal.impact_score >= cond["min_impact"]:
                if signal.direction == cond["direction"]:
                    if "eligible_types" not in cond or signal.event_type in cond["eligible_types"]:
                        return rule["action"]
        return "NONE"

    def run_stress(self, signal: RiskSignalSchema, portfolio_id: str, run_mode: str = "auto"):
        action = self.check_trigger(signal)
        if action not in ["TRIGGER_SYSTEMIC", "TRIGGER_TARGETED"] and run_mode == "auto":
            return None # Not triggered
            
        # Get scenario
        scenario_name = signal.event_type
        base_shock = self.scenarios.get(scenario_name, {})
        
        # Scale by multiplier (multiplier = clip(impact_score/8, 0.5, 1.5))
        multiplier = max(0.5, min(1.5, signal.impact_score / 8.0))
        
        shocks_applied = {}
        for k, v in base_shock.items():
            if isinstance(v, (int, float)):
                if k == "pd_multiplier":
                    # For PD multiplier, we might want a different scaling, e.g., 1 + (v-1)*multiplier
                    shocks_applied[k] = 1.0 + (v - 1.0) * multiplier
                else:
                    shocks_applied[k] = v * multiplier
            elif isinstance(v, dict):
                shocks_applied[k] = {sk: sv * multiplier for sk, sv in v.items()}
                
        # Load positions
        positions = self.db.query(PortfolioPosition).filter(PortfolioPosition.portfolio_id == portfolio_id).all()
        
        run_id = str(uuid.uuid4())
        results = []
        
        portfolio_val_before = 0.0
        portfolio_val_after = 0.0
        
        for pos in positions:
            pos_dict = {
                "asset_class": pos.asset_class,
                "instrument_type": pos.instrument_type,
                "current_value": pos.current_value,
                "notional": pos.notional,
                "exposure": pos.exposure,
                "modified_duration": pos.modified_duration,
                "convexity": pos.convexity,
                "spread_duration": pos.spread_duration,
                "pd_base": pos.pd_base,
                "lgd": pos.lgd,
                "beta": pos.beta,
                "dv01": pos.dv01,
                "delta": pos.delta,
                "ticker": pos.ticker,
                "sector": pos.sector
            }
            
            # Apply sector overrides if systemic
            pos_shock = dict(shocks_applied)
            
            if "sector_overrides" in pos_shock and pos.sector in pos_shock["sector_overrides"]:
                pos_shock["equity_shock_pct"] = pos_shock["sector_overrides"][pos.sector]
                
            # If targeted credit event, apply shocks mainly to primary_company
            if action == "TRIGGER_TARGETED":
                if pos.ticker != signal.primary_company:
                    # Apply spillover only
                    pos_shock["equity_shock_pct"] = 0.0
                    pos_shock["pd_multiplier"] = 1.0
                    spillover = pos_shock.get("sector_spillover_bp", 0.0)
                    pos_shock["credit_spread_bp"] = spillover if pos.sector == signal.scope else 0.0
            
            res = self.valuation_engine.calculate_delta(pos_dict, pos_shock)
            
            portfolio_val_before += res["value_before"]
            portfolio_val_after += res["value_after"]
            
            results.append(StressPositionResult(
                result_id=str(uuid.uuid4()),
                run_id=run_id,
                position_id=pos.position_id,
                value_before=res["value_before"],
                value_after=res["value_after"],
                loss=res["loss"],
                driver_breakdown=res["driver_breakdown"]
            ))
            
        absolute_loss = portfolio_val_before - portfolio_val_after
        pct_loss = (absolute_loss / portfolio_val_before) if portfolio_val_before > 0 else 0.0
        
        run_record = StressRun(
            run_id=run_id,
            trigger_signal_id=signal.signal_id,
            event_type=signal.event_type,
            impact_score=signal.impact_score,
            multiplier=multiplier,
            scenario_name=scenario_name,
            shocks_applied=shocks_applied,
            portfolio_id=portfolio_id,
            portfolio_value_before=portfolio_val_before,
            portfolio_value_after=portfolio_val_after,
            absolute_loss=absolute_loss,
            pct_loss=pct_loss,
            run_mode=run_mode
        )
        
        self.db.add(run_record)
        self.db.bulk_save_objects(results)
        self.db.commit()
        
        return run_id
