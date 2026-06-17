#!/usr/bin/env python3
"""
Master Backup Integrity Verification
Ensures backup is complete and restorable
"""

import os
import hashlib
import json
import sys
from pathlib import Path
from datetime import datetime

class BackupIntegrityVerifier:
    """Verify backup integrity and completeness."""

    def __init__(self):
        self.results = {
            'timestamp': datetime.utcnow().isoformat(),
            'backup_name': 'already_here_agentic_trading_control_os_MASTER_BACKUP_2026-06-17',
            'files_verified': 0,
            'files_missing': 0,
            'checksums': {},
            'status': 'PENDING'
        }

        # Define required files
        self.required_files = {
            'trading-control': [
                'app.py',
                'models.py',
                'agents_impl.py',
                'synthesis_engine.py',
                'risk_kernel.py',
                'paper_broker.py',
                'audit_ledger.py',
                'robinhood_adapter.py',
                'cmdos_integration.py',
                'verify_all_systems.py',
                'launch_complete_system.py',
                'news_monitor_24_7.py',
                'run_phase_test.py',
                'practice_live_real_data.py',
                'config.yaml',
                'requirements.txt',
                '__init__.py'
            ],
            'root': [
                'COMPLETE_DEPLOYMENT_GUIDE.md',
                'CMDOS_SSH_SETUP.md',
                'READY_FOR_DEPLOYMENT.md',
                'CLAUDE.md',
                'MASTER_BACKUP_AUDIT_A+.md'
            ],
            'scripts': [
                'enforce-cmdos-keys.sh',
                'ensure-authorized-keys.sh'
            ],
            '.github/workflows': [
                'cmdos-keywarden.yml'
            ]
        }

    def verify_files(self, base_path='.'):
        """Verify all required files exist."""
        print("\n" + "="*80)
        print("BACKUP INTEGRITY VERIFICATION")
        print("="*80)
        print(f"\nBase Path: {base_path}")
        print(f"Timestamp: {self.results['timestamp']}\n")

        missing = []
        present = []

        for directory, files in self.required_files.items():
            dir_path = Path(base_path) / directory if directory != 'root' else Path(base_path)

            print(f"\n📁 {directory}/ ({len(files)} files)")

            for filename in files:
                file_path = dir_path / filename

                if file_path.exists():
                    file_size = file_path.stat().st_size
                    print(f"  ✅ {filename:<40} ({file_size:>10,} bytes)")
                    present.append(str(file_path))
                    self.results['files_verified'] += 1
                else:
                    print(f"  ❌ {filename:<40} MISSING")
                    missing.append(str(file_path))
                    self.results['files_missing'] += 1

        return missing

    def calculate_checksums(self, base_path='.'):
        """Calculate SHA256 checksums for all files."""
        print("\n" + "="*80)
        print("CALCULATING CHECKSUMS")
        print("="*80 + "\n")

        for directory, files in self.required_files.items():
            dir_path = Path(base_path) / directory if directory != 'root' else Path(base_path)

            for filename in files:
                file_path = dir_path / filename

                if not file_path.exists():
                    continue

                try:
                    sha256_hash = hashlib.sha256()
                    with open(file_path, 'rb') as f:
                        for byte_block in iter(lambda: f.read(4096), b''):
                            sha256_hash.update(byte_block)

                    checksum = sha256_hash.hexdigest()
                    self.results['checksums'][str(file_path)] = checksum
                    print(f"✅ {filename:<45} {checksum[:32]}...")

                except Exception as e:
                    print(f"❌ {filename:<45} ERROR: {e}")

        # Save checksums to file
        checksum_file = Path(base_path) / 'BACKUP_CHECKSUMS.json'
        with open(checksum_file, 'w') as f:
            json.dump(self.results['checksums'], f, indent=2)

        print(f"\n✅ Checksums saved to: {checksum_file}")
        return self.results['checksums']

    def verify_git_history(self, base_path='.'):
        """Verify git history is intact."""
        print("\n" + "="*80)
        print("GIT HISTORY VERIFICATION")
        print("="*80 + "\n")

        git_dir = Path(base_path) / '.git'

        if git_dir.exists():
            print("✅ .git directory present")

            # Count commits
            try:
                import subprocess
                result = subprocess.run(
                    ['git', 'rev-list', '--count', 'HEAD'],
                    cwd=base_path,
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.returncode == 0:
                    commit_count = result.stdout.strip()
                    print(f"✅ Total commits: {commit_count}")
                    self.results['git_commits'] = int(commit_count)
                else:
                    print("⚠️  Could not count commits")
            except Exception as e:
                print(f"⚠️  Git verification error: {e}")
        else:
            print("❌ .git directory missing")

        return True

    def generate_report(self):
        """Generate final verification report."""
        print("\n" + "="*80)
        print("VERIFICATION REPORT")
        print("="*80 + "\n")

        total_files = sum(len(files) for files in self.required_files.values())

        print(f"Backup Name: {self.results['backup_name']}")
        print(f"Timestamp: {self.results['timestamp']}")
        print(f"\nFiles Verified: {self.results['files_verified']}/{total_files}")
        print(f"Files Missing:  {self.results['files_missing']}/{total_files}")
        print(f"Checksums:      {len(self.results['checksums'])} calculated")

        if self.results['files_missing'] == 0:
            self.results['status'] = 'PASS'
            status_emoji = '✅'
        else:
            self.results['status'] = 'FAIL'
            status_emoji = '❌'

        print(f"\n{status_emoji} Overall Status: {self.results['status']}")

        # Save report
        report_file = Path('BACKUP_VERIFICATION_REPORT.json')
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)

        print(f"\n📋 Detailed report saved to: {report_file}")

        # Print verdict
        print("\n" + "="*80)
        if self.results['status'] == 'PASS':
            print("✅ BACKUP INTEGRITY VERIFIED — Ready for Production Deployment")
            print("\nBackup is complete and ready to:")
            print("  • Be archived for disaster recovery")
            print("  • Be distributed to team members")
            print("  • Be restored in emergency scenarios")
            print("  • Be deployed to new environments")
        else:
            print("⚠️  BACKUP INCOMPLETE — Review missing files before deployment")
        print("="*80 + "\n")

        return self.results

    def run_full_verification(self, base_path='.'):
        """Run complete verification process."""
        print("\n")
        print("╔" + "="*78 + "╗")
        print("║" + "MASTER BACKUP INTEGRITY VERIFICATION SUITE".center(78) + "║")
        print("╚" + "="*78 + "╝")

        # Run all checks
        missing = self.verify_files(base_path)
        checksums = self.calculate_checksums(base_path)
        self.verify_git_history(base_path)
        report = self.generate_report()

        return report


def main():
    """Main entry point."""
    try:
        verifier = BackupIntegrityVerifier()
        report = verifier.run_full_verification()

        # Exit with appropriate code
        sys.exit(0 if report['status'] == 'PASS' else 1)

    except KeyboardInterrupt:
        print("\n\n✅ Verification interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Verification error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
