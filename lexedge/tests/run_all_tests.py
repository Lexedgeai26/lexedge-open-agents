#!/usr/bin/env python
"""
Convenience script to run all lexedge tests.
This script runs all test files in the proper order and provides a summary.
"""

import sys
import os
import subprocess
import time
from typing import List, Tuple

def run_test(test_file: str) -> Tuple[bool, str, float]:
    """Run a single test file and return results."""
    print(f"\n{'='*60}")
    print(f"🧪 Running: {test_file}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout per test
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Print the output
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"⚠️ Warnings/Errors:\n{result.stderr}")
        
        success = result.returncode == 0
        
        if success:
            print(f"✅ {test_file} PASSED in {duration:.1f}s")
        else:
            print(f"❌ {test_file} FAILED in {duration:.1f}s (exit code: {result.returncode})")
        
        return success, result.stderr, duration
        
    except subprocess.TimeoutExpired:
        print(f"⏰ {test_file} TIMED OUT after 120 seconds")
        return False, "Test timed out", 120.0
    except Exception as e:
        print(f"💥 {test_file} CRASHED: {str(e)}")
        return False, str(e), 0.0

def main():
    """Main function to run all tests."""
    print("🚀 lexedge Test Suite Runner")
    print("Running all tests in the recommended order...")
    
    # Get the current directory (should be lexedge/tests/)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define tests in logical order (relative to current directory)
    test_files = [
        "test_session_management.py",           # Foundation: session management
        "test_agent_pusher_basic.py",          # Core: basic agent pusher
        "test_websocket_integration.py",        # Integration: WebSocket functionality
        "test_job_cancellation.py",            # Specific: job tool cancellation
        "test_universal_cancellation.py",       # Comprehensive: universal system
        "test_documentation_examples.py",      # Validation: docs examples
    ]
    
    # Convert to absolute paths
    test_files = [os.path.join(current_dir, f) for f in test_files]
    
    # Verify all test files exist
    missing_files = []
    for test_file in test_files:
        if not os.path.exists(test_file):
            missing_files.append(test_file)
    
    if missing_files:
        print(f"❌ Missing test files: {missing_files}")
        sys.exit(1)
    
    # Run all tests
    results = []
    total_start_time = time.time()
    
    for test_file in test_files:
        success, stderr, duration = run_test(test_file)
        results.append({
            'file': os.path.basename(test_file),
            'success': success,
            'stderr': stderr,
            'duration': duration
        })
        
        # Brief pause between tests
        time.sleep(1)
    
    total_duration = time.time() - total_start_time
    
    # Print summary
    print(f"\n{'='*80}")
    print("📊 TEST SUMMARY")
    print(f"{'='*80}")
    
    passed = sum(1 for r in results if r['success'])
    failed = len(results) - passed
    
    print(f"📋 Total Tests: {len(results)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"⏱️ Total Time: {total_duration:.1f}s")
    print()
    
    # Detailed results
    for result in results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        test_name = result['file'].replace('.py', '').replace('test_', '')
        print(f"{status} {test_name:<25} ({result['duration']:.1f}s)")
    
    # Show failures in detail
    failures = [r for r in results if not r['success']]
    if failures:
        print(f"\n🚨 FAILURE DETAILS:")
        for failure in failures:
            print(f"\n❌ {failure['file']}:")
            print(f"   Error: {failure['stderr'][:200]}...")
    
    print(f"\n{'='*80}")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED! The cancellation system is working perfectly!")
        print("🚀 Ready for production deployment.")
    else:
        print(f"⚠️ {failed} test(s) failed. Please check the errors above.")
        print("🔧 Fix the issues and run the tests again.")
    
    print(f"{'='*80}")
    
    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main() 