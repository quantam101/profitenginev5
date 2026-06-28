"""
SQLAlchemy ORM models for AH-POS system.
Past Performance, Capture Intelligence, Pricing & Wrap-Rate.
"""
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime, Date, Boolean, Text, ForeignKey,
    Index, ARRAY, DECIMAL, JSON, func
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

Base = declarative_base()

# ============================================================================
# AUDIT MIXIN
# ============================================================================

class AuditMixin:
    """Adds created_by, created_at, updated_by, updated_at to models."""
    created_by = Column(String(255), default='system')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(String(255), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# PART 1: PAST PERFORMANCE MODELS
# ============================================================================

class Agency(Base):
    __tablename__ = 'agencies'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    duns_number = Column(String(20))
    cage_code = Column(String(10), index=True)
    sam_gov_entity_id = Column(String(100))
    website = Column(String(255))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    past_performance = relationship('PastPerformanceContract', back_populates='agency')
    solicitations = relationship('Solicitation', back_populates='agency')
    incumbents = relationship('IncumbentContract', back_populates='agency')

    def __repr__(self):
        return f"<Agency {self.name}>"


class NAICSCode(Base):
    __tablename__ = 'naics_codes'

    id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    is_small_business = Column(Boolean)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<NAICS {self.code}: {self.title}>"


class PSCCode(Base):
    __tablename__ = 'psc_codes'

    id = Column(Integer, primary_key=True)
    code = Column(String(10), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PSC {self.code}: {self.title}>"


class ContractType(Base):
    __tablename__ = 'contract_types'

    id = Column(Integer, primary_key=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    rate_model = Column(String(50))

    def __repr__(self):
        return f"<ContractType {self.code}>"


class PastPerformanceContract(Base):
    __tablename__ = 'past_performance_contracts'

    id = Column(Integer, primary_key=True)
    contract_id = Column(String(100), unique=True, nullable=False, index=True)
    contract_number = Column(String(100))
    agency_id = Column(Integer, ForeignKey('agencies.id'))
    agency_name = Column(String(255))
    naics_id = Column(Integer, ForeignKey('naics_codes.id'))
    naics_code = Column(String(10), index=True)
    psc_id = Column(Integer, ForeignKey('psc_codes.id'))
    psc_code = Column(String(10), index=True)
    contract_type_id = Column(Integer, ForeignKey('contract_types.id'))
    contract_type = Column(String(20))

    # Dates
    award_date = Column(Date, index=True)
    start_date = Column(Date)
    end_date = Column(Date, index=True)
    completion_date = Column(Date)

    # Performance Metrics
    total_contract_value = Column(DECIMAL(15, 2))
    amount_spent = Column(DECIMAL(15, 2))
    on_time_percent = Column(Numeric(5, 2))
    cost_variance_percent = Column(Numeric(6, 2))
    quality_rating = Column(Numeric(3, 1))
    rework_percent = Column(Numeric(5, 2))
    re_award = Column(Boolean, default=False)

    # Customer Contact
    customer_agency = Column(String(255))
    customer_poc_name = Column(String(255))
    customer_poc_email = Column(String(255))
    customer_poc_phone = Column(String(20))
    ordering_officer_name = Column(String(255))
    ordering_officer_email = Column(String(255))

    # Opportunity Context
    incumbent_contractor = Column(String(255))
    number_of_competitors = Column(Integer)
    win_strategy = Column(Text)

    # Narrative & Proof
    executive_summary = Column(Text)
    relevant_experience_narrative = Column(Text)
    performance_narrative = Column(Text)

    # Document References
    proof_documents_url = Column(Text)
    cpars_url = Column(String(255))
    sam_gov_url = Column(String(255))

    notes = Column(Text)

    # Audit Trail
    created_by = Column(String(255), default='system')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(String(255), default='system')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    agency = relationship('Agency', back_populates='past_performance')
    references = relationship('PastPerformanceReference', back_populates='contract')

    def __repr__(self):
        return f"<PastPerformance {self.contract_id}>"


class PastPerformanceReference(Base):
    __tablename__ = 'past_performance_references'

    id = Column(Integer, primary_key=True)
    contract_id = Column(Integer, ForeignKey('past_performance_contracts.id'), nullable=False)
    reference_name = Column(String(255))
    reference_email = Column(String(255))
    reference_phone = Column(String(20))
    reference_title = Column(String(255))
    contact_frequency = Column(String(100))
    reference_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)

    contract = relationship('PastPerformanceContract', back_populates='references')

    def __repr__(self):
        return f"<Reference {self.reference_name}>"


# ============================================================================
# PART 2: CAPTURE INTELLIGENCE MODELS
# ============================================================================

class Solicitation(Base):
    __tablename__ = 'solicitations'

    id = Column(Integer, primary_key=True)
    solicitation_id = Column(String(100), unique=True, nullable=False)
    solicitation_number = Column(String(100))
    title = Column(String(500))
    description = Column(Text)
    agency_id = Column(Integer, ForeignKey('agencies.id'))
    agency_name = Column(String(255))

    # NAICS & PSC
    naics_codes = Column(ARRAY(String), index=True)
    psc_codes = Column(ARRAY(String))

    # Key Dates
    posted_date = Column(Date, index=True)
    response_deadline = Column(Date, index=True)

    # Set-Asides & Restrictions
    small_business_setaside = Column(Boolean)
    wosb_setaside = Column(Boolean)
    hubzone_setaside = Column(Boolean)
    setaside_8a = Column(Boolean)
    veteran_owned = Column(Boolean)
    service_disabled_veteran = Column(Boolean)

    # Opportunity Details
    estimated_value = Column(DECIMAL(15, 2))
    contract_type = Column(String(20))
    place_of_performance = Column(String(255))

    # Scoring
    relevance_score = Column(Integer)
    timeline_score = Column(Integer)
    agency_fit_score = Column(Integer)
    incumbent_risk_score = Column(Integer)

    # Status
    status = Column(String(50), default='open', index=True)
    awarded_to = Column(String(255))
    awarded_date = Column(Date)

    # Links
    sam_gov_url = Column(String(255))
    fbo_url = Column(String(255))

    # Audit Trail
    first_seen_date = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    alert_generated = Column(Boolean, default=False)

    # Relationships
    agency = relationship('Agency', back_populates='solicitations')

    @property
    def opportunity_score(self) -> int:
        """Calculate opportunity score from component scores."""
        if not all([self.relevance_score, self.timeline_score, self.agency_fit_score]):
            return 0
        return int(
            self.relevance_score * 0.35 +
            self.timeline_score * 0.30 +
            self.agency_fit_score * 0.25 +
            (100 - self.incumbent_risk_score) * 0.10
        )

    def __repr__(self):
        return f"<Solicitation {self.solicitation_number}>"


class IncumbentContract(Base):
    __tablename__ = 'incumbent_contracts'

    id = Column(Integer, primary_key=True)
    contract_id = Column(String(100), unique=True, nullable=False)
    contract_number = Column(String(100))
    agency_id = Column(Integer, ForeignKey('agencies.id'))
    agency_name = Column(String(255))
    incumbent_contractor = Column(String(255))
    incumbent_duns = Column(String(20))

    # Dates
    award_date = Column(Date)
    expiration_date = Column(Date, index=True)

    # Contract Details
    naics_code = Column(String(10))
    psc_code = Column(String(10))
    contract_value = Column(DECIMAL(15, 2))
    contract_type = Column(String(20))

    # Performance Data
    cpars_rating = Column(Numeric(3, 1))
    cpars_last_reviewed = Column(Date)

    # Recompete Intelligence
    recompete_likely = Column(Boolean)
    recompete_comments = Column(Text)

    # Links
    sam_gov_url = Column(String(255))
    cpars_url = Column(String(255))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    agency = relationship('Agency', back_populates='incumbents')

    def __repr__(self):
        return f"<Incumbent {self.incumbent_contractor}>"


class AgencyBudgetTrend(Base):
    __tablename__ = 'agency_budget_trends'

    id = Column(Integer, primary_key=True)
    agency_id = Column(Integer, ForeignKey('agencies.id'), nullable=False)
    naics_code = Column(String(10), nullable=False)
    fiscal_year = Column(Integer)
    contract_count = Column(Integer)
    total_awards = Column(DECIMAL(15, 2))
    avg_contract_value = Column(DECIMAL(15, 2))
    yoy_growth_percent = Column(Numeric(6, 2))
    created_at = Column(DateTime, default=datetime.utcnow)

    Index('idx_budget_agency_naics_fy', 'agency_id', 'naics_code', 'fiscal_year', unique=True)

    def __repr__(self):
        return f"<BudgetTrend {self.agency_id} {self.naics_code} {self.fiscal_year}>"


class Alert(Base):
    __tablename__ = 'alerts'

    id = Column(Integer, primary_key=True)
    alert_type = Column(String(50))  # 'new_solicitation', 'recompete_window', etc.
    severity = Column(String(20))  # 'high', 'medium', 'low'
    title = Column(String(500))
    description = Column(Text)
    solicitation_id = Column(Integer, ForeignKey('solicitations.id'))
    incumbent_id = Column(Integer, ForeignKey('incumbent_contracts.id'))
    agency_id = Column(Integer, ForeignKey('agencies.id'))

    # Context
    naics_code = Column(String(10))
    estimated_value = Column(DECIMAL(15, 2))
    opportunity_score = Column(Integer)

    # Status
    status = Column(String(50), default='new', index=True)
    acknowledged_by = Column(String(255))
    acknowledged_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Alert {self.alert_type}: {self.title}>"


# ============================================================================
# PART 3: PRICING & WRAP-RATE MODELS
# ============================================================================

class LaborCategory(Base):
    __tablename__ = 'labor_categories'

    id = Column(Integer, primary_key=True)
    category_code = Column(String(50), nullable=False)
    category_name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    gsa_schedule_number = Column(String(50))

    # Rates by Year
    loaded_rate_2024 = Column(DECIMAL(10, 2))
    loaded_rate_2025 = Column(DECIMAL(10, 2))
    loaded_rate_2026 = Column(DECIMAL(10, 2))

    # Rate Components
    base_hourly_rate = Column(DECIMAL(10, 2))
    burden_rate_percent = Column(Numeric(5, 2))
    overhead_percent = Column(Numeric(5, 2))
    ga_percent = Column(Numeric(5, 2))
    profit_percent = Column(Numeric(5, 2))

    # Contract Type Variations
    ffp_rate = Column(DECIMAL(10, 2))
    tm_rate = Column(DECIMAL(10, 2))
    idiq_rate = Column(DECIMAL(10, 2))

    # Minimum Experience
    min_years_experience = Column(Integer)
    required_clearance = Column(String(100))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_current_rate(self) -> Decimal:
        """Get the most recent loaded rate."""
        for rate in [self.loaded_rate_2026, self.loaded_rate_2025, self.loaded_rate_2024]:
            if rate:
                return rate
        return self.base_hourly_rate

    def __repr__(self):
        return f"<LaborCategory {self.category_code}>"


class IndirectCostRate(Base):
    __tablename__ = 'indirect_cost_rates'

    id = Column(Integer, primary_key=True)
    contractor_name = Column(String(255), nullable=False)
    duns_number = Column(String(20))
    cage_code = Column(String(10))

    # Rate Information
    indirect_type = Column(String(50))  # 'overhead', 'g_and_a', 'fringe'
    rate_percent = Column(Numeric(5, 2))
    base_amount = Column(DECIMAL(15, 2))

    # Dates
    effective_from = Column(Date, index=True)
    effective_to = Column(Date)

    # Status
    status = Column(String(50), index=True)  # 'provisional', 'negotiated', 'final'
    dcaa_approved = Column(Boolean)
    dcaa_audit_date = Column(Date)

    # References
    dcaa_decision_url = Column(String(255))
    notes = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<IndirectCostRate {self.contractor_name} {self.indirect_type}>"


class RateCard(Base):
    __tablename__ = 'rate_cards'

    id = Column(Integer, primary_key=True)
    rate_card_name = Column(String(255), nullable=False)
    gsa_schedule_number = Column(String(50))
    effective_from = Column(Date, index=True)
    effective_to = Column(Date)

    # Contractor Info
    contractor_name = Column(String(255))
    duns_number = Column(String(20))
    cage_code = Column(String(10))

    # Rates
    min_labor_rate = Column(DECIMAL(10, 2))
    max_labor_rate = Column(DECIMAL(10, 2))
    avg_labor_rate = Column(DECIMAL(10, 2))

    # Overhead
    overhead_rate_percent = Column(Numeric(5, 2))
    g_and_a_percent = Column(Numeric(5, 2))

    # Profit
    profit_percent_ffp = Column(Numeric(5, 2))
    profit_percent_tm = Column(Numeric(5, 2))
    profit_percent_idiq = Column(Numeric(5, 2))

    # Historical Tracking
    previous_rate_card_id = Column(Integer, ForeignKey('rate_cards.id'))
    cola_increase_percent = Column(Numeric(5, 2))

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<RateCard {self.rate_card_name}>"


class CostAnalysis(Base):
    __tablename__ = 'cost_analyses'

    id = Column(Integer, primary_key=True)
    proposal_id = Column(String(100), nullable=False, index=True)
    solicitation_id = Column(String(100))
    opportunity_id = Column(Integer, ForeignKey('solicitations.id'))

    # Proposal Info
    proposal_name = Column(String(500))
    proposal_date = Column(Date, default=date.today)
    contractor_name = Column(String(255))

    # Cost Elements
    total_labor_hours = Column(DECIMAL(10, 2))
    total_labor_cost = Column(DECIMAL(15, 2))
    total_material_cost = Column(DECIMAL(15, 2))
    total_overhead = Column(DECIMAL(15, 2))
    total_ga = Column(DECIMAL(15, 2))
    total_profit = Column(DECIMAL(15, 2))

    # Totals
    subtotal_cost = Column(DECIMAL(15, 2))
    total_contract_value = Column(DECIMAL(15, 2))

    # Contract Type & Terms
    contract_type = Column(String(20))
    contract_duration_months = Column(Integer)

    # Compliance
    dcaa_compliant = Column(Boolean)
    sf1411_certified = Column(Boolean)
    risk_buffer_percent = Column(Numeric(5, 2))
    profit_margin_percent = Column(Numeric(5, 2))

    # Audit Trail
    created_by = Column(String(255), default='system')
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_by = Column(String(255))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = Column(Text)

    line_items = relationship('CostAnalysisLineItem', back_populates='cost_analysis')

    def __repr__(self):
        return f"<CostAnalysis {self.proposal_id}>"


class CostAnalysisLineItem(Base):
    __tablename__ = 'cost_analysis_line_items'

    id = Column(Integer, primary_key=True)
    cost_analysis_id = Column(Integer, ForeignKey('cost_analyses.id'), nullable=False)
    line_number = Column(Integer)
    labor_category_id = Column(Integer, ForeignKey('labor_categories.id'))
    labor_category = Column(String(255))

    # Quantities
    hours_per_month = Column(DECIMAL(10, 2))
    months = Column(Integer)
    total_hours = Column(DECIMAL(10, 2))

    # Rates & Costs
    hourly_rate = Column(DECIMAL(10, 2))
    extended_cost = Column(DECIMAL(15, 2))

    # Burden
    burden_percent = Column(Numeric(5, 2))
    burden_amount = Column(DECIMAL(15, 2))

    created_at = Column(DateTime, default=datetime.utcnow)

    cost_analysis = relationship('CostAnalysis', back_populates='line_items')

    def __repr__(self):
        return f"<LineItem {self.line_number}>"


class AuditLog(Base):
    __tablename__ = 'audit_log'

    id = Column(Integer, primary_key=True)
    table_name = Column(String(100), index=True)
    record_id = Column(Integer)
    action = Column(String(50))  # 'INSERT', 'UPDATE', 'DELETE'
    changed_fields = Column(JSON)
    changed_by = Column(String(255))
    changed_at = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<AuditLog {self.action} {self.table_name}>"


# ============================================================================
# PYDANTIC SCHEMAS FOR API SERIALIZATION
# ============================================================================

class SolicitationSchema(BaseModel):
    id: int
    solicitation_number: str
    title: str
    agency_name: str
    naics_codes: List[str] = []
    response_deadline: Optional[date] = None
    estimated_value: Optional[Decimal] = None
    opportunity_score: int = 0
    status: str = 'open'

    class Config:
        from_attributes = True


class PastPerformanceSchema(BaseModel):
    id: int
    contract_id: str
    contract_number: Optional[str] = None
    agency_name: str
    naics_code: Optional[str] = None
    contract_type: str
    total_contract_value: Optional[Decimal] = None
    award_date: Optional[date] = None
    end_date: Optional[date] = None
    on_time_percent: Optional[Decimal] = None
    quality_rating: Optional[Decimal] = None
    executive_summary: Optional[str] = None

    class Config:
        from_attributes = True


class AlertSchema(BaseModel):
    id: int
    alert_type: str
    severity: str
    title: str
    description: Optional[str] = None
    created_at: datetime
    status: str = 'new'

    class Config:
        from_attributes = True


class LaborCategorySchema(BaseModel):
    id: int
    category_code: str
    category_name: str
    loaded_rate_2026: Optional[Decimal] = None
    ffp_rate: Optional[Decimal] = None
    tm_rate: Optional[Decimal] = None

    class Config:
        from_attributes = True
