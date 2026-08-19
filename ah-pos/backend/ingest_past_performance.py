"""
Import Past Performance contracts from CSV or manual entry.
Idempotent — running twice produces the same database state.
"""
import csv
import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional
from pathlib import Path
import json

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from models import (
    Base, Agency, NAICSCode, PSCCode, ContractType, PastPerformanceContract,
    PastPerformanceReference, AuditLog
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PastPerformanceIngester:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)

    def ingest_from_csv(self, csv_file: Path, ingested_by: str = 'ingest_script'):
        """
        Import past performance contracts from CSV.

        Expected CSV columns:
        contract_id, contract_number, agency_name, naics_code, psc_code, contract_type,
        award_date, start_date, end_date, total_contract_value, amount_spent,
        on_time_percent, cost_variance_percent, quality_rating, customer_poc_name,
        customer_poc_email, ordering_officer_name, executive_summary
        """
        session = self.Session()
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            if not rows:
                logger.warning(f"CSV file {csv_file} is empty")
                return

            logger.info(f"Found {len(rows)} contracts in CSV")

            for idx, row in enumerate(rows, 1):
                try:
                    self._import_contract_row(session, row, ingested_by)
                except Exception as e:
                    logger.error(f"Row {idx}: {str(e)}")
                    session.rollback()
                    continue

            session.commit()
            logger.info(f"Successfully imported {len(rows)} contracts")

        except Exception as e:
            logger.error(f"Failed to ingest CSV: {e}")
            session.rollback()
            raise
        finally:
            session.close()

    def _import_contract_row(self, session, row: Dict, ingested_by: str):
        """Import a single contract row from CSV."""
        contract_id = row.get('contract_id', '').strip()
        if not contract_id:
            raise ValueError("contract_id is required")

        # Check if contract already exists (idempotency)
        existing = session.query(PastPerformanceContract).filter_by(contract_id=contract_id).first()
        if existing:
            logger.debug(f"Contract {contract_id} already exists, skipping")
            return

        # Get or create agency
        agency_name = row.get('agency_name', '').strip()
        agency = session.query(Agency).filter_by(name=agency_name).first()
        if not agency and agency_name:
            agency = Agency(name=agency_name)
            session.add(agency)
            session.flush()
            logger.debug(f"Created agency: {agency_name}")

        # Get or create NAICS
        naics_code = row.get('naics_code', '').strip()
        naics = None
        if naics_code:
            naics = session.query(NAICSCode).filter_by(code=naics_code).first()
            if not naics:
                # Create minimal NAICS entry (should be bulk-loaded from NAICS file)
                naics = NAICSCode(code=naics_code, title=f"NAICS {naics_code}")
                session.add(naics)
                session.flush()

        # Get or create PSC
        psc_code = row.get('psc_code', '').strip()
        psc = None
        if psc_code:
            psc = session.query(PSCCode).filter_by(code=psc_code).first()
            if not psc:
                psc = PSCCode(code=psc_code, title=f"PSC {psc_code}")
                session.add(psc)
                session.flush()

        # Get or create contract type
        contract_type_code = row.get('contract_type', '').strip().upper()
        contract_type = None
        if contract_type_code:
            contract_type = session.query(ContractType).filter_by(code=contract_type_code).first()

        # Parse dates
        award_date = self._parse_date(row.get('award_date'))
        start_date = self._parse_date(row.get('start_date'))
        end_date = self._parse_date(row.get('end_date'))

        # Parse decimals
        total_value = self._parse_decimal(row.get('total_contract_value'))
        amount_spent = self._parse_decimal(row.get('amount_spent'))
        on_time = self._parse_decimal(row.get('on_time_percent'))
        cost_var = self._parse_decimal(row.get('cost_variance_percent'))
        quality = self._parse_decimal(row.get('quality_rating'))

        # Create contract
        contract = PastPerformanceContract(
            contract_id=contract_id,
            contract_number=row.get('contract_number', '').strip(),
            agency_id=agency.id if agency else None,
            agency_name=agency_name,
            naics_id=naics.id if naics else None,
            naics_code=naics_code,
            psc_id=psc.id if psc else None,
            psc_code=psc_code,
            contract_type_id=contract_type.id if contract_type else None,
            contract_type=contract_type_code,

            award_date=award_date,
            start_date=start_date,
            end_date=end_date,

            total_contract_value=total_value,
            amount_spent=amount_spent,
            on_time_percent=on_time,
            cost_variance_percent=cost_var,
            quality_rating=quality,

            customer_agency=row.get('customer_agency', '').strip(),
            customer_poc_name=row.get('customer_poc_name', '').strip(),
            customer_poc_email=row.get('customer_poc_email', '').strip(),
            ordering_officer_name=row.get('ordering_officer_name', '').strip(),

            incumbent_contractor=row.get('incumbent_contractor', '').strip(),
            number_of_competitors=self._parse_int(row.get('number_of_competitors')),

            executive_summary=row.get('executive_summary', '').strip(),
            relevant_experience_narrative=row.get('relevant_experience_narrative', '').strip(),
            performance_narrative=row.get('performance_narrative', '').strip(),

            proof_documents_url=row.get('proof_documents_url', '').strip(),
            cpars_url=row.get('cpars_url', '').strip(),

            created_by=ingested_by,
            updated_by=ingested_by,
            notes=row.get('notes', '').strip(),
        )

        session.add(contract)
        session.flush()

        # Add references if provided
        references_json = row.get('references_json', '').strip()
        if references_json:
            try:
                references = json.loads(references_json)
                for ref in references:
                    ref_obj = PastPerformanceReference(
                        contract_id=contract.id,
                        reference_name=ref.get('name'),
                        reference_email=ref.get('email'),
                        reference_phone=ref.get('phone'),
                        reference_title=ref.get('title'),
                    )
                    session.add(ref_obj)
            except json.JSONDecodeError:
                logger.warning(f"Invalid references JSON for {contract_id}")

        logger.info(f"Imported contract: {contract_id}")

    def _parse_date(self, value: Optional[str]) -> Optional[date]:
        if not value or not value.strip():
            return None
        for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y'):
            try:
                return datetime.strptime(value.strip(), fmt).date()
            except ValueError:
                continue
        logger.warning(f"Could not parse date: {value}")
        return None

    def _parse_decimal(self, value: Optional[str]) -> Optional[Decimal]:
        if not value or not value.strip():
            return None
        try:
            return Decimal(value.strip().replace(',', ''))
        except:
            logger.warning(f"Could not parse decimal: {value}")
            return None

    def _parse_int(self, value: Optional[str]) -> Optional[int]:
        if not value or not value.strip():
            return None
        try:
            return int(value.strip())
        except:
            return None

    def bootstrap_naics_codes(self, naics_csv: Path):
        """Load all NAICS codes from official CSV."""
        session = self.Session()
        try:
            with open(naics_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    code = row.get('code', '').strip()
                    if not code:
                        continue

                    existing = session.query(NAICSCode).filter_by(code=code).first()
                    if existing:
                        continue

                    naics = NAICSCode(
                        code=code,
                        title=row.get('title', ''),
                        description=row.get('description', ''),
                        is_small_business=row.get('is_small_business', '').lower() == 'true'
                    )
                    session.add(naics)

            session.commit()
            logger.info("Loaded NAICS codes")
        except FileNotFoundError:
            logger.warning(f"NAICS file not found: {naics_csv}")
        finally:
            session.close()

    def get_past_performance_for_naics(self, naics_code: str, years_back: int = 10) -> List[PastPerformanceContract]:
        """Query past performance contracts for a specific NAICS code."""
        session = self.Session()
        try:
            cutoff_date = date.today().replace(year=date.today().year - years_back)
            contracts = session.query(PastPerformanceContract).filter(
                PastPerformanceContract.naics_code == naics_code,
                PastPerformanceContract.end_date >= cutoff_date
            ).order_by(PastPerformanceContract.end_date.desc()).all()
            return contracts
        finally:
            session.close()


def main():
    import os
    from dotenv import load_dotenv

    load_dotenv()
    database_url = os.getenv('DATABASE_URL', '').strip()
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")

    ingester = PastPerformanceIngester(database_url)

    # Bootstrap NAICS codes (one-time)
    # naics_file = Path(__file__).parent / 'data' / 'naics_2024.csv'
    # ingester.bootstrap_naics_codes(naics_file)

    # Import contracts
    csv_file = Path(__file__).parent / 'data' / 'past_performance.csv'
    if csv_file.exists():
        ingester.ingest_from_csv(csv_file, ingested_by='admin')
    else:
        logger.info(f"No CSV file at {csv_file}")


if __name__ == '__main__':
    main()
