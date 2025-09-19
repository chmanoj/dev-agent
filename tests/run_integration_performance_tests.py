"""Comprehensive test runner for integration and performance tests."""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


class IntegrationPerformanceTestRunner:
    """Runner for integration and performance tests."""

    def __init__(self, verbose: bool = False):
        """Initialize test runner.

        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose
        self.test_results = {}
        self.start_time = None
        self.end_time = None

    def run_all_tests(self) -> dict[str, Any]:
        """Run all integration and performance tests.

        Returns:
            Dictionary with test results
        """
        print("🚀 Starting comprehensive integration and performance tests...")
        self.start_time = time.time()

        # Test categories to run
        test_categories = [
            ("Large Codebase Integration", "test_large_codebase_integration.py"),
            ("End-to-End Workflow", "test_end_to_end_workflow.py"),
            ("Performance Benchmarks", "test_performance_benchmarks.py"),
            ("Existing Performance Tests", "test_indexing_engine_performance.py"),
            ("Workflow Orchestration", "test_workflow_orchestration.py"),
        ]

        results = {}

        for category_name, test_file in test_categories:
            print(f"\n{'=' * 60}")
            print(f"Running {category_name}")
            print(f"{'=' * 60}")

            result = self._run_test_file(test_file)
            results[category_name] = result

            if result["success"]:
                print(f"✅ {category_name} - PASSED")
            else:
                print(f"❌ {category_name} - FAILED")
                if self.verbose:
                    print(f"Error: {result.get('error', 'Unknown error')}")

        self.end_time = time.time()
        self.test_results = results

        return self._generate_summary()

    def run_specific_tests(self, test_names: list[str]) -> dict[str, Any]:
        """Run specific test categories.

        Args:
            test_names: List of test category names to run

        Returns:
            Dictionary with test results
        """
        print(f"🎯 Running specific tests: {', '.join(test_names)}")
        self.start_time = time.time()

        # Map test names to files
        test_mapping = {
            "large_codebase": "test_large_codebase_integration.py",
            "end_to_end": "test_end_to_end_workflow.py",
            "performance": "test_performance_benchmarks.py",
            "existing_performance": "test_indexing_engine_performance.py",
            "workflow": "test_workflow_orchestration.py",
        }

        results = {}

        for test_name in test_names:
            if test_name not in test_mapping:
                print(f"⚠️  Unknown test: {test_name}")
                continue

            test_file = test_mapping[test_name]
            print(f"\n{'=' * 60}")
            print(f"Running {test_name}")
            print(f"{'=' * 60}")

            result = self._run_test_file(test_file)
            results[test_name] = result

            if result["success"]:
                print(f"✅ {test_name} - PASSED")
            else:
                print(f"❌ {test_name} - FAILED")

        self.end_time = time.time()
        self.test_results = results

        return self._generate_summary()

    def run_quick_tests(self) -> dict[str, Any]:
        """Run a quick subset of tests for CI/development.

        Returns:
            Dictionary with test results
        """
        print("⚡ Running quick integration and performance tests...")
        self.start_time = time.time()

        # Quick test subset - smaller, faster tests
        quick_tests = [
            (
                "Quick Performance",
                "test_indexing_engine_performance.py",
                ["test_small_codebase_performance"],
            ),
            (
                "Basic Workflow",
                "test_workflow_orchestration.py",
                ["test_complete_workflow_integration"],
            ),
        ]

        results = {}

        for category_name, test_file, specific_tests in quick_tests:
            print(f"\n{'=' * 40}")
            print(f"Running {category_name}")
            print(f"{'=' * 40}")

            result = self._run_specific_test_methods(test_file, specific_tests)
            results[category_name] = result

            if result["success"]:
                print(f"✅ {category_name} - PASSED")
            else:
                print(f"❌ {category_name} - FAILED")

        self.end_time = time.time()
        self.test_results = results

        return self._generate_summary()

    def _run_test_file(self, test_file: str) -> dict[str, Any]:
        """Run a specific test file.

        Args:
            test_file: Name of the test file to run

        Returns:
            Dictionary with test result information
        """
        test_path = Path(__file__).parent / test_file

        if not test_path.exists():
            return {
                "success": False,
                "error": f"Test file not found: {test_file}",
                "duration": 0,
                "output": "",
            }

        start_time = time.time()

        try:
            # Run pytest on the specific file
            cmd = [
                sys.executable,
                "-m",
                "pytest",
                str(test_path),
                "-v",
                "--tb=short",
                "--disable-warnings",
            ]

            if self.verbose:
                cmd.append("-s")

            result = subprocess.run(
                cmd,
                check=False,
                capture_output=True,
                text=True,
                timeout=1800,  # 30 minute timeout
            )

            duration = time.time() - start_time

            return {
                "success": result.returncode == 0,
                "duration": duration,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None,
                "return_code": result.returncode,
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Test timed out after 30 minutes",
                "duration": time.time() - start_time,
                "output": "",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time,
                "output": "",
            }

    def _run_specific_test_methods(
        self, test_file: str, test_methods: list[str]
    ) -> dict[str, Any]:
        """Run specific test methods from a test file.

        Args:
            test_file: Name of the test file
            test_methods: List of specific test method names

        Returns:
            Dictionary with test result information
        """
        test_path = Path(__file__).parent / test_file

        if not test_path.exists():
            return {
                "success": False,
                "error": f"Test file not found: {test_file}",
                "duration": 0,
                "output": "",
            }

        start_time = time.time()

        try:
            # Run specific test methods
            test_specs = [f"{test_path}::{method}" for method in test_methods]

            cmd = (
                [sys.executable, "-m", "pytest"]
                + test_specs
                + ["-v", "--tb=short", "--disable-warnings"]
            )

            if self.verbose:
                cmd.append("-s")

            result = subprocess.run(
                cmd,
                check=False,
                capture_output=True,
                text=True,
                timeout=900,  # 15 minute timeout for quick tests
            )

            duration = time.time() - start_time

            return {
                "success": result.returncode == 0,
                "duration": duration,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None,
                "return_code": result.returncode,
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Test timed out",
                "duration": time.time() - start_time,
                "output": "",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time,
                "output": "",
            }

    def _generate_summary(self) -> dict[str, Any]:
        """Generate test summary.

        Returns:
            Dictionary with comprehensive test summary
        """
        if not self.test_results:
            return {"error": "No test results available"}

        total_duration = (
            self.end_time - self.start_time if self.end_time and self.start_time else 0
        )

        # Calculate statistics
        total_tests = len(self.test_results)
        passed_tests = sum(
            1 for result in self.test_results.values() if result["success"]
        )
        failed_tests = total_tests - passed_tests

        total_test_duration = sum(
            result["duration"] for result in self.test_results.values()
        )
        avg_test_duration = total_test_duration / total_tests if total_tests > 0 else 0

        # Generate summary
        summary = {
            "overall_success": failed_tests == 0,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests / total_tests * 100)
            if total_tests > 0
            else 0,
            "total_duration": total_duration,
            "total_test_duration": total_test_duration,
            "avg_test_duration": avg_test_duration,
            "test_results": self.test_results,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        # Print summary
        self._print_summary(summary)

        return summary

    def _print_summary(self, summary: dict[str, Any]) -> None:
        """Print test summary to console.

        Args:
            summary: Test summary dictionary
        """
        print(f"\n{'=' * 80}")
        print("🏁 TEST SUMMARY")
        print(f"{'=' * 80}")

        # Overall status
        if summary["overall_success"]:
            print("🎉 ALL TESTS PASSED!")
        else:
            print("💥 SOME TESTS FAILED!")

        print("\n📊 Statistics:")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Passed: {summary['passed_tests']} ✅")
        print(f"   Failed: {summary['failed_tests']} ❌")
        print(f"   Success Rate: {summary['success_rate']:.1f}%")

        print("\n⏱️  Timing:")
        print(f"   Total Duration: {summary['total_duration']:.2f} seconds")
        print(f"   Test Duration: {summary['total_test_duration']:.2f} seconds")
        print(f"   Average per Test: {summary['avg_test_duration']:.2f} seconds")

        print("\n📋 Individual Test Results:")
        for test_name, result in summary["test_results"].items():
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            duration = result["duration"]
            print(f"   {test_name}: {status} ({duration:.2f}s)")

            if not result["success"] and result.get("error"):
                print(f"      Error: {result['error']}")

        print(f"\n🕐 Completed at: {summary['timestamp']}")
        print(f"{'=' * 80}")

    def save_results(self, output_file: str) -> None:
        """Save test results to file.

        Args:
            output_file: Path to output file
        """
        if not self.test_results:
            print("⚠️  No test results to save")
            return

        summary = self._generate_summary()

        try:
            with open(output_file, "w") as f:
                json.dump(summary, f, indent=2)
            print(f"💾 Test results saved to: {output_file}")
        except Exception as e:
            print(f"❌ Failed to save results: {e}")

    def check_requirements(self) -> bool:
        """Check if all required dependencies are available.

        Returns:
            True if all requirements are met
        """
        print("🔍 Checking test requirements...")

        required_packages = ["pytest", "psutil", "pandas", "numpy"]

        missing_packages = []

        for package in required_packages:
            try:
                __import__(package)
                print(f"   ✅ {package}")
            except ImportError:
                print(f"   ❌ {package} - MISSING")
                missing_packages.append(package)

        if missing_packages:
            print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
            print("Install with: pip install " + " ".join(missing_packages))
            return False

        print("✅ All requirements satisfied!")
        return True


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(
        description="Run integration and performance tests"
    )

    parser.add_argument(
        "--mode",
        choices=["all", "quick", "specific"],
        default="all",
        help="Test mode to run",
    )

    parser.add_argument(
        "--tests", nargs="+", help="Specific tests to run (for specific mode)"
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    parser.add_argument(
        "--output", "-o", help="Output file for test results (JSON format)"
    )

    parser.add_argument(
        "--check-requirements", action="store_true", help="Check requirements and exit"
    )

    args = parser.parse_args()

    # Initialize test runner
    runner = IntegrationPerformanceTestRunner(verbose=args.verbose)

    # Check requirements if requested
    if args.check_requirements:
        if runner.check_requirements():
            sys.exit(0)
        else:
            sys.exit(1)

    # Check requirements before running tests
    if not runner.check_requirements():
        print("❌ Requirements not met. Use --check-requirements for details.")
        sys.exit(1)

    # Run tests based on mode
    try:
        if args.mode == "all":
            summary = runner.run_all_tests()
        elif args.mode == "quick":
            summary = runner.run_quick_tests()
        elif args.mode == "specific":
            if not args.tests:
                print("❌ Specific mode requires --tests argument")
                sys.exit(1)
            summary = runner.run_specific_tests(args.tests)
        else:
            print(f"❌ Unknown mode: {args.mode}")
            sys.exit(1)

        # Save results if requested
        if args.output:
            runner.save_results(args.output)

        # Exit with appropriate code
        if summary["overall_success"]:
            print("\n🎉 All tests completed successfully!")
            sys.exit(0)
        else:
            print(f"\n💥 {summary['failed_tests']} test(s) failed!")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Test runner failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
