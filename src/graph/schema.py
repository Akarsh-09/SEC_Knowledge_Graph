"""Validated graph nodes; observations and claims require page-level provenance."""
from typing import Literal
from pydantic import BaseModel, Field, model_validator

class CompanyNode(BaseModel):
    id: str
    node_type: Literal['Company'] = 'Company'
    ticker: str
    name: str
    sector: str
    cik: str

class CanonicalMetricNode(BaseModel):
    id: str
    node_type: Literal['CanonicalMetric'] = 'CanonicalMetric'
    name: str

class FiscalPeriodNode(BaseModel):
    id: str
    node_type: Literal['FiscalPeriod'] = 'FiscalPeriod'

class ExternalEntityNode(BaseModel):
    id: str
    node_type: Literal['ExternalEntity'] = 'ExternalEntity'
    name: str

class DocumentNode(BaseModel):
    id: str
    node_type: Literal['Document'] = 'Document'
    filename: str

class Provenance(BaseModel):
    id: str
    company_id: str
    source_doc: str
    page_num: int = Field(ge=1)
    section: str = Field(min_length=1)
    snippet: str = Field(min_length=1)

class MetricObservationNode(Provenance):
    status: Literal['active', 'superseded', 'corroborating'] = 'active'
    analytical_value_usd: float = 0.0
    raw_label: str = ''
    @model_validator(mode='after')
    def analytical_value(self):
        self.analytical_value_usd = abs(self.value_usd) if self.metric_id == 'METRIC:CAPEX' else self.value_usd
        return self

    node_type: Literal['MetricObservation'] = 'MetricObservation'
    metric_id: str
    period: str
    value_raw: float
    scale_multiplier: float
    value_usd: float
    unit: str = 'USD'
    audited: bool = False

class RelationClaimNode(Provenance):
    status: Literal['active', 'superseded', 'corroborating'] = 'active'
    audit_scope: str | None = None
    evidence_kind: Literal['text','signature_asset'] = 'text'
    node_type: Literal['RelationClaim'] = 'RelationClaim'
    relation_type: str
    target_id: str
    target_name: str
