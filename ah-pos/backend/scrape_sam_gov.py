"""
Daily SAM.gov Solicitation Scraper
Fetches new solicitations, scores them, and generates alerts.
Idempotent — running twice = same database state.
"""
import logging
import os
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
import json
from decimal import Decimal

import requests
from sqlalchemy import create_engine, and_, func
from sqlalchemy.orm import sessionmaker

from models import (
    Base, Agency, Solicitation, Alert, PastPerformanceContract, IncumbentContract
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# SAM.gov API endpoints (public, no auth required)
SAM_API_BASE = "https://api.sam.gov/prod/opportunities/v1/search"
USASPENDING_API_BASE = "https://api.usaspending.gov/api/v2"


class SolicitationScraper:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)

    def scrape_sam_gov(self, naics_codes: List[str], max_results: int = 500) -> List[Dict]:
        """
        Fetch solicitations from SAM.gov API.
        Query params: NAICS codes, status = 'PREVIEW' or 'PUBLISHED'
        Returns list of parsed opportunities.
        """
        logger.info(f"Scraping SAM.gov for NAICS: {naics_codes}")

        opportunities = []
        for naics in naics_codes:
            try:
                params = {
                    'naicsCodes': naics,
                    'postedFrom': (datetime.now() - timedelta(days=7)).isoformat(),
                    'limit': max_results,
                    'sort': '-postedDate',
                }

                response = requests.get(SAM_API_BASE, params=params, timeout=30)
                response.raise_for_status()

                data = response.json()
                opportunities.extend(data.get('opportunitiesData', []))
                logger.info(f"Found {len(data.get('opportunitiesData', []))} opportunities for NAICS {naics}")

            except requests.RequestException as e:
                logger.error(f"SAM.gov API error for {naics}: {e}")
                continue

        return opportunities

    def parse_opportunity(self, opp: Dict) -> Dict:
        """
        Parse SAM.gov opportunity JSON into our schema.
        """
        try:
            # Parse dates
            posted_date = None
            if opp.get('postedDate'):
                try:
                    posted_date = datetime.fromisoformat(opp['postedDate']).date()
                except:
                    pass

            response_deadline = None
            if opp.get('responseDeadLine'):
                try:
                    response_deadline = datetime.fromisoformat(opp['responseDeadLine']).date()
                except:
                    pass

            # Parse value
            estimated_value = None
            if opp.get('estimatedAmount'):
                try:
                    estimated_value = Decimal(str(opp['estimatedAmount']))
                except:
                    pass

            # Extract NAICS codes
            naics_codes = []
            if opp.get('naicsCodes'):
                if isinstance(opp['naicsCodes'], list):
                    naics_codes = opp['naicsCodes']
                elif isinstance(opp['naicsCodes'], str):
                    naics_codes = [opp['naicsCodes']]

            # Extract PSC codes
            psc_codes = []
            if opp.get('pscCodes'):
                if isinstance(opp['pscCodes'], list):
                    psc_codes = opp['pscCodes']
                elif isinstance(opp['pscCodes'], str):
                    psc_codes = [opp['pscCodes']]

            parsed = {
                'solicitation_id': opp.get('opportunityID', ''),
                'solicitation_number': opp.get('solicitationNumber', ''),
                'title': opp.get('title', '')[:500],
                'description': opp.get('description', ''),
                'agency_name': opp.get('organizationName', ''),
                'naics_codes': naics_codes,
                'psc_codes': psc_codes,
                'posted_date': posted_date,
                'response_deadline': response_deadline,
                'estimated_value': estimated_value,
                'contract_type': opp.get('awardContractTypeName', ''),
                'place_of_performance': opp.get('placeOfPerformance', ''),
                'small_business_setaside': opp.get('setAsideName', '').lower().find('small business') >= 0,
                'sam_gov_url': f"https://sam.gov/opportunity/{opp.get('opportunityID', '')}",
            }

            return parsed
        except Exception as e:
            logger.error(f"Error parsing opportunity: {e}")
            return None

    def score_opportunity(self, session, opportunity: Dict) -> Dict:
        """
        Calculate opportunity scores:
        - relevance_score (0-100): how well NAICS matches our past performance
        - timeline_score (0-100): days to close (more days = lower urgency but more time to prepare)
        - agency_fit_score (0-100): how much past performance with this agency
        - incumbent_risk_score (0-100): likelihood incumbent will win again
        """
        naics_codes = opportunity.get('naics_codes', [])
        agency_name = opportunity.get('agency_name', '')
        response_deadline = opportunity.get('response_deadline')

        # Relevance: check if we have past performance in these NAICS
        relevance_score = 0
        past_perf_count = 0
        if naics_codes:
            for naics in naics_codes:
                pp = session.query(PastPerformanceContract).filter(
                    PastPerformanceContract.naics_code == naics
                ).count()
                past_perf_count += pp
            relevance_score = min(100, int((past_perf_count / len(naics_codes)) * 50)) if naics_codes else 0

        # Timeline: higher score if more time, but capped
        timeline_score = 50  # default
        if response_deadline:
            days_left = (response_deadline - date.today()).days
            if days_left > 60:
                timeline_score = 100
            elif days_left > 30:
                timeline_score = 75
            elif days_left > 14:
                timeline_score = 50
            elif days_left > 7:
                timeline_score = 30
            else:
                timeline_score = 10

        # Agency fit: check past performance with this agency
        agency_fit_score = 0
        if agency_name:
            agency = session.query(Agency).filter_by(name=agency_name).first()
            if agency:
                pp_with_agency = session.query(PastPerformanceContract).filter(
                    PastPerformanceContract.agency_id == agency.id
                ).count()
                agency_fit_score = min(100, pp_with_agency * 20)

        # Incumbent risk: check if current contract is held by known incumbent
        incumbent_risk_score = 50  # assume moderate risk
        if naics_codes and agency_name:
            agency = session.query(Agency).filter_by(name=agency_name).first()
            if agency:
                incumbents = session.query(IncumbentContract).filter(
                    IncumbentContract.agency_id == agency.id,
                    IncumbentContract.naics_code.in_(naics_codes)
                ).count()
                if incumbents > 0:
                    incumbent_risk_score = 75  # high risk if incumbent contract exists
                else:
                    incumbent_risk_score = 30  # lower risk if new opportunity

        opportunity['relevance_score'] = relevance_score
        opportunity['timeline_score'] = timeline_score
        opportunity['agency_fit_score'] = agency_fit_score
        opportunity['incumbent_risk_score'] = incumbent_risk_score

        return opportunity

    def import_opportunities(self, opportunities: List[Dict], created_by: str = 'scraper'):
        """
        Import opportunities into database.
        Only inserts if solicitation_id not already present (idempotency).
        """
        session = self.Session()
        imported = 0
        updated = 0

        try:
            for opp in opportunities:
                parsed = self.parse_opportunity(opp)
                if not parsed:
                    continue

                solicitation_id = parsed['solicitation_id']

                # Check if already exists
                existing = session.query(Solicitation).filter_by(
                    solicitation_id=solicitation_id
                ).first()

                if existing:
                    # Update last_updated timestamp
                    existing.last_updated = datetime.utcnow()
                    updated += 1
                    logger.debug(f"Solicitation {solicitation_id} already exists, updating timestamp")
                    continue

                # Get or create agency
                agency = None
                if parsed['agency_name']:
                    agency = session.query(Agency).filter_by(name=parsed['agency_name']).first()
                    if not agency:
                        agency = Agency(name=parsed['agency_name'])
                        session.add(agency)
                        session.flush()

                # Score the opportunity
                parsed = self.score_opportunity(session, parsed)

                # Create solicitation
                solicitation = Solicitation(
                    solicitation_id=parsed['solicitation_id'],
                    solicitation_number=parsed['solicitation_number'],
                    title=parsed['title'],
                    description=parsed['description'],
                    agency_id=agency.id if agency else None,
                    agency_name=parsed['agency_name'],
                    naics_codes=parsed['naics_codes'],
                    psc_codes=parsed['psc_codes'],
                    posted_date=parsed['posted_date'],
                    response_deadline=parsed['response_deadline'],
                    estimated_value=parsed['estimated_value'],
                    contract_type=parsed['contract_type'],
                    place_of_performance=parsed['place_of_performance'],
                    small_business_setaside=parsed.get('small_business_setaside', False),
                    relevance_score=parsed.get('relevance_score', 0),
                    timeline_score=parsed.get('timeline_score', 50),
                    agency_fit_score=parsed.get('agency_fit_score', 0),
                    incumbent_risk_score=parsed.get('incumbent_risk_score', 50),
                    sam_gov_url=parsed['sam_gov_url'],
                    status='open',
                    first_seen_date=datetime.utcnow(),
                    alert_generated=False,
                )

                session.add(solicitation)
                session.flush()

                # Generate alert if high-priority
                if solicitation.opportunity_score >= 70:
                    alert = Alert(
                        alert_type='new_solicitation',
                        severity='high' if solicitation.opportunity_score >= 80 else 'medium',
                        title=f"High-priority opportunity: {solicitation.title[:100]}",
                        description=f"Score: {solicitation.opportunity_score}, Days to close: {solicitation.days_to_close}",
                        solicitation_id=solicitation.id,
                        agency_id=agency.id if agency else None,
                        naics_code=parsed['naics_codes'][0] if parsed['naics_codes'] else None,
                        estimated_value=parsed['estimated_value'],
                        opportunity_score=solicitation.opportunity_score,
                    )
                    session.add(alert)
                    solicitation.alert_generated = True

                imported += 1
                logger.info(f"Imported: {solicitation_id} (score: {solicitation.opportunity_score})")

            session.commit()
            logger.info(f"Import complete: {imported} new, {updated} updated")

        except Exception as e:
            logger.error(f"Error importing opportunities: {e}")
            session.rollback()
            raise
        finally:
            session.close()

    def run_daily_sync(self, naics_codes: List[str]):
        """
        Full daily sync: scrape → parse → score → import → generate alerts
        """
        logger.info("=== Starting daily SAM.gov sync ===")

        # Scrape SAM.gov
        opportunities = self.scrape_sam_gov(naics_codes)
        logger.info(f"Downloaded {len(opportunities)} opportunities")

        # Import into database
        self.import_opportunities(opportunities)

        logger.info("=== Daily sync complete ===")

        return len(opportunities)


def main():
    from dotenv import load_dotenv

    load_dotenv()
    database_url = os.getenv('DATABASE_URL', '').strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")

    # Example NAICS codes to monitor
    naics_codes = ['541611', '541512', '541330']  # IT services, IT consulting, etc.

    scraper = SolicitationScraper(database_url)
    scraper.run_daily_sync(naics_codes)


if __name__ == '__main__':
    main()
