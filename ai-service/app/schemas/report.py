from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class SituationReportResult(BaseModel):
    """
    Automated civil-defense and meteorological situation brief
    """
    cyclone_id: str = Field(..., description="Target cyclone identifier")
    cyclone_name: str = Field(..., description="Storm name")
    generated_at: datetime = Field(..., description="UTC generation timestamp")
    executive_summary: str = Field(..., description="High-level operational overview for emergency managers")
    key_threats: List[str] = Field(default_factory=list, description="Primary catastrophic threats (wind, surge, flood)")
    recommended_actions: List[str] = Field(default_factory=list, description="Recommended civil protection operations")
    meteorological_synthesis: str = Field(..., description="Technical explanation of atmospheric dynamics")


class ReportGenerateRequest(BaseModel):
    """
    Request payload for on-demand report synthesis
    """
    cyclone_id: str = Field(..., description="Identifier of target cyclone")
    cyclone_name: Optional[str] = Field(default="Cyclone", description="Storm name")
