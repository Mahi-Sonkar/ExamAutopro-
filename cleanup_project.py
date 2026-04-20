"""
Targeted Project Cleanup
Remove only essential unwanted files while preserving core functionality
"""

import os
import shutil
from typing import List

class TargetedCleanup:
    """Targeted cleanup of unwanted files"""
    
    def __init__(self, project_root: str = "d:\\ExamAutoPro"):
        self.project_root = project_root
        self.removed_files = []
        self.errors = []
    
    def cleanup_essential_files(self) -> dict:
        """Remove only essential unwanted files"""
        print("=== TARGETED PROJECT CLEANUP ===")
        
        # 1. Remove test files from project root
        self._remove_test_files()
        
        # 2. Remove temporary analysis files from project root
        self._remove_temp_analysis_files()
        
        # 3. Remove __pycache__ directories from project root only
        self._remove_pycache_directories()
        
        # 4. Remove development-specific files
        self._remove_dev_files()
        
        return {
            'removed_files': self.removed_files,
            'errors': self.errors,
            'total_removed': len(self.removed_files)
        }
    
    def _remove_test_files(self) -> None:
        """Remove test files from project root"""
        test_files = [
            'test_evaluation_simple.py',
            'test_ocr_pipeline.py',
            'test_pages.py',
            'test_pdf_analysis.py',
            'test_question_extraction.py',
            'test_urls.py',
            'quick_test.py',
            'temp_check.py',
            'verify_nlp.py'
        ]
        
        for test_file in test_files:
            file_path = os.path.join(self.project_root, test_file)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    self.removed_files.append(file_path)
                    print(f"✅ Removed test file: {test_file}")
                except Exception as e:
                    self.errors.append(f"Failed to remove {test_file}: {e}")
    
    def _remove_temp_analysis_files(self) -> None:
        """Remove temporary analysis files from project root"""
        temp_files = [
            'api_analysis.py',
            'check_pdf_analysis.py',
            'error_analysis.py',
            'final_project_analysis.py',
            'fix_remaining_issues.py',
            'system_analysis_and_fixes.py',
            'project_cleanup_analysis.py'
        ]
        
        for temp_file in temp_files:
            file_path = os.path.join(self.project_root, temp_file)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    self.removed_files.append(file_path)
                    print(f"✅ Removed temp file: {temp_file}")
                except Exception as e:
                    self.errors.append(f"Failed to remove {temp_file}: {e}")
    
    def _remove_pycache_directories(self) -> None:
        """Remove __pycache__ directories from project root only"""
        for item in os.listdir(self.project_root):
            item_path = os.path.join(self.project_root, item)
            
            if item == '__pycache__' and os.path.isdir(item_path):
                try:
                    shutil.rmtree(item_path)
                    self.removed_files.append(item_path)
                    print(f"✅ Removed __pycache__ directory")
                except Exception as e:
                    self.errors.append(f"Failed to remove __pycache__: {e}")
            
            # Also check app directories for __pycache__
            elif os.path.isdir(item_path) and not item.startswith('.') and item != 'venv':
                app_pycache = os.path.join(item_path, '__pycache__')
                if os.path.exists(app_pycache):
                    try:
                        shutil.rmtree(app_pycache)
                        self.removed_files.append(app_pycache)
                        print(f"✅ Removed __pycache__ from {item}")
                    except Exception as e:
                        self.errors.append(f"Failed to remove __pycache__ from {item}: {e}")
    
    def _remove_dev_files(self) -> None:
        """Remove development-specific files"""
        dev_files = [
            'settings_dev.py',
            'views_dev.py'
        ]
        
        # Check in specific directories
        for root, dirs, files in os.walk(self.project_root):
            # Skip venv and hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'venv']
            
            for file in files:
                if file in dev_files:
                    file_path = os.path.join(root, file)
                    try:
                        os.remove(file_path)
                        self.removed_files.append(file_path)
                        print(f"✅ Removed dev file: {file}")
                    except Exception as e:
                        self.errors.append(f"Failed to remove {file}: {e}")
    
    def verify_essential_files_remain(self) -> dict:
        """Verify essential files still exist"""
        print("\n=== VERIFYING ESSENTIAL FILES ===")
        
        essential_files = [
            'manage.py',
            'requirements.txt',
            'README.md',
            'ExamAutoPro/settings.py',
            'ExamAutoPro/urls.py',
            'accounts/models.py',
            'accounts/views.py',
            'pdf_analysis/models.py',
            'pdf_analysis/views.py',
            'evaluation/models.py',
            'evaluation/views.py',
            'core/api_views.py',
            'pdf_analysis/free_evaluation_system.py',
            'pdf_analysis/enhanced_evaluation_system.py'
        ]
        
        missing_files = []
        existing_files = []
        
        for file in essential_files:
            file_path = os.path.join(self.project_root, file)
            if os.path.exists(file_path):
                existing_files.append(file)
                print(f"✅ {file}")
            else:
                missing_files.append(file)
                print(f"❌ {file}")
        
        return {
            'existing_files': existing_files,
            'missing_files': missing_files,
            'total_essential': len(essential_files),
            'verified': len(missing_files) == 0
        }
    
    def generate_cleanup_report(self) -> dict:
        """Generate final cleanup report"""
        print("\n=== GENERATING CLEANUP REPORT ===")
        
        # Perform cleanup
        cleanup_result = self.cleanup_essential_files()
        
        # Verify essential files
        verification = self.verify_essential_files_remain()
        
        report = {
            'cleanup_result': cleanup_result,
            'verification': verification,
            'summary': {
                'total_files_removed': cleanup_result['total_removed'],
                'total_errors': len(cleanup_result['errors']),
                'essential_files_verified': verification['verified'],
                'cleanup_successful': cleanup_result['total_removed'] > 0 and len(cleanup_result['errors']) == 0
            }
        }
        
        return report


def run_targeted_cleanup():
    """Run targeted project cleanup"""
    print("=== TARGETED PROJECT CLEANUP ===")
    
    cleanup = TargetedCleanup()
    report = cleanup.generate_cleanup_report()
    
    print(f"\n=== CLEANUP SUMMARY ===")
    print(f"Files Removed: {report['summary']['total_files_removed']}")
    print(f"Errors: {report['summary']['total_errors']}")
    print(f"Essential Files Verified: {report['summary']['essential_files_verified']}")
    print(f"Cleanup Successful: {report['summary']['cleanup_successful']}")
    
    if report['summary']['cleanup_successful']:
        print("\n✅ Project cleanup completed successfully!")
        print("🎯 Project is now clean and production-ready")
    else:
        print("\n⚠️ Some cleanup operations failed")
        print("🔧 Review errors and retry if needed")
    
    return report


if __name__ == "__main__":
    run_targeted_cleanup()
