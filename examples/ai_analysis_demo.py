#!/usr/bin/env python3
"""
Demo script for the AI-powered code analysis engine.

This script demonstrates how to use the AI analysis engine to perform
comprehensive code analysis including quality, security, performance,
and architectural analysis.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from dev_agent.analysis.ai_analysis_engine import AIAnalysisEngine
from dev_agent.indexing.indexing_engine import IndexingEngine
from dev_agent.services.azure_openai_service import AzureOpenAIService


def create_sample_project() -> str:
    """Create a sample project with various code issues for analysis."""
    temp_dir = tempfile.mkdtemp()
    project_path = Path(temp_dir)
    
    # Create project structure
    (project_path / "src").mkdir()
    (project_path / "src" / "models").mkdir()
    (project_path / "src" / "services").mkdir()
    (project_path / "tests").mkdir()
    
    # Create a file with quality issues
    quality_issues_file = project_path / "src" / "quality_issues.py"
    quality_issues_file.write_text('''
"""Module with various code quality issues."""

import os
import sys

# Global variables (code smell)
GLOBAL_COUNTER = 0
GLOBAL_DATA = {}

class GodClass:
    """A class that does too many things (violation of SRP)."""
    
    def __init__(self, name, email, phone, address, age, preferences, settings, config):
        """Constructor with too many parameters."""
        self.name = name
        self.email = email
        self.phone = phone
        self.address = address
        self.age = age
        self.preferences = preferences
        self.settings = settings
        self.config = config
        self.data = []
        self.cache = {}
        self.logger = None
    
    def very_long_method_that_does_too_much(self):
        """This method is way too long and does too many things."""
        # Data validation
        if not self.name:
            raise ValueError("Name is required")
        if not self.email:
            raise ValueError("Email is required")
        if "@" not in self.email:
            raise ValueError("Invalid email")
        
        # Data processing
        processed_data = []
        for i in range(100):
            if i % 2 == 0:
                for j in range(50):
                    if j % 3 == 0:
                        for k in range(10):
                            if k % 5 == 0:
                                processed_data.append(i * j * k)
        
        # Logging
        print(f"Processing data for {self.name}")
        print(f"Email: {self.email}")
        print(f"Phone: {self.phone}")
        
        # File operations
        for item in processed_data:
            with open(f"data_{item}.txt", "w") as f:
                f.write(str(item))
        
        # More processing
        result = ""
        for item in processed_data:
            result += str(item) + ","  # Inefficient string concatenation
        
        # Database operations (simulated)
        for item in processed_data:
            self.save_to_database(item)
        
        # More lines to make it even longer
        temp_list = []
        for i in range(1000):
            temp_list.append(i * 2)
        
        final_result = []
        for item in temp_list:
            if item > 100:
                final_result.append(item)
        
        return final_result
    
    def save_to_database(self, data):
        """Simulate database save."""
        pass
    
    # Many more methods to make it a god class
    def method_1(self): pass
    def method_2(self): pass
    def method_3(self): pass
    def method_4(self): pass
    def method_5(self): pass
    def method_6(self): pass
    def method_7(self): pass
    def method_8(self): pass
    def method_9(self): pass
    def method_10(self): pass
    def method_11(self): pass
    def method_12(self): pass
    def method_13(self): pass
    def method_14(self): pass
    def method_15(self): pass
    def method_16(self): pass
    def method_17(self): pass
    def method_18(self): pass
    def method_19(self): pass
    def method_20(self): pass

def unused_function():
    """This function is never called."""
    return "This is dead code"

def function_with_nested_loops(data):
    """Function with performance issues due to nested loops."""
    result = []
    for i in data:
        for j in data:
            for k in data:
                result.append(i + j + k)
    return result
''')
    
    # Create a file with security issues
    security_issues_file = project_path / "src" / "security_issues.py"
    security_issues_file.write_text('''
"""Module with various security vulnerabilities."""

import os
import sqlite3
import hashlib

# Hardcoded secrets (security vulnerability)
API_KEY = "sk-1234567890abcdef1234567890abcdef"
DATABASE_PASSWORD = "supersecret123"
SECRET_TOKEN = "abc123def456ghi789"

class UserManager:
    """User management with security issues."""
    
    def authenticate_user(self, username, password):
        """Vulnerable authentication method."""
        # Weak password hashing
        password_hash = hashlib.md5(password.encode()).hexdigest()
        
        # SQL injection vulnerability
        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password_hash}'"
        
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute(query)  # Vulnerable to SQL injection
        
        user = cursor.fetchone()
        conn.close()
        
        return user is not None
    
    def get_user_data(self, user_id):
        """Method with SQL injection vulnerability."""
        query = "SELECT * FROM users WHERE id = %s" % user_id
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute(query)
        return cursor.fetchall()
    
    def process_user_input(self, user_code):
        """Dangerous code execution."""
        # Code injection vulnerability
        result = eval(user_code)  # Never do this!
        return result
    
    def log_user_activity(self, username, password, action):
        """Logging sensitive information."""
        # Information exposure through logs
        print(f"User {username} with password {password} performed {action}")
        
        # Write to log file
        with open("activity.log", "a") as f:
            f.write(f"User: {username}, Password: {password}, Action: {action}\\n")
    
    def generate_session_token(self):
        """Weak random number generation."""
        import random
        # Predictable random number generation
        token = str(random.randint(1000000, 9999999))
        return token
''')
    
    # Create a file with performance issues
    performance_issues_file = project_path / "src" / "performance_issues.py"
    performance_issues_file.write_text('''
"""Module with various performance bottlenecks."""

import requests
import time

class DataProcessor:
    """Class with performance issues."""
    
    def __init__(self):
        self.data = []
        self.cache = {}
    
    def inefficient_data_processing(self, items):
        """Method with algorithmic performance issues."""
        result = []
        
        # O(n³) algorithm - very inefficient
        for i in items:
            for j in items:
                for k in items:
                    if i + j + k > 100:
                        result.append((i, j, k))
        
        return result
    
    def inefficient_string_building(self, words):
        """Inefficient string concatenation."""
        result = ""
        for word in words:
            result += word + " "  # Inefficient string concatenation
        return result
    
    def inefficient_file_operations(self, data_list):
        """File I/O in loops."""
        results = []
        for i, data in enumerate(data_list):
            # File operations in loop
            with open(f"temp_{i}.txt", "w") as f:
                f.write(str(data))
            
            # Read it back immediately
            with open(f"temp_{i}.txt", "r") as f:
                content = f.read()
                results.append(content)
        
        return results
    
    def inefficient_network_calls(self, urls):
        """Synchronous network calls in loop."""
        results = []
        for url in urls:
            # Synchronous network call in loop
            response = requests.get(url)
            results.append(response.text)
        return results
    
    def inefficient_database_queries(self, user_ids):
        """N+1 query problem simulation."""
        users = []
        for user_id in user_ids:
            # This simulates the N+1 query problem
            user = self.get_user_by_id(user_id)
            users.append(user)
        return users
    
    def get_user_by_id(self, user_id):
        """Simulate database query."""
        time.sleep(0.01)  # Simulate database latency
        return {"id": user_id, "name": f"User {user_id}"}
    
    def memory_inefficient_processing(self, size):
        """Memory inefficient operations."""
        # Creating large lists unnecessarily
        large_list = [i for i in range(size)]
        
        # Processing in memory instead of streaming
        processed = []
        for item in large_list:
            processed.append(item * 2)
        
        return processed
''')
    
    # Create a file with architectural issues
    architectural_issues_file = project_path / "src" / "architectural_issues.py"
    architectural_issues_file.write_text('''
"""Module with architectural violations."""

# Circular dependency simulation
from .models.user import User  # This would create circular dependency
from .services.user_service import UserService

class PresentationLayer:
    """Presentation layer that violates layer separation."""
    
    def __init__(self):
        # Direct dependency on data layer (violation)
        from .models.database import Database
        self.db = Database()
        
        # Should go through business layer instead
        self.user_service = UserService()
    
    def display_user(self, user_id):
        """Method that mixes concerns."""
        # Data access (should be in data layer)
        user_data = self.db.get_user(user_id)
        
        # Business logic (should be in business layer)
        if user_data['age'] < 18:
            user_data['restricted'] = True
        
        # Presentation logic (correct layer)
        return f"User: {user_data['name']} ({user_data['age']} years old)"

class TightlyCoupledClass:
    """Class with high coupling."""
    
    def __init__(self):
        # Too many dependencies
        from .services.email_service import EmailService
        from .services.sms_service import SMSService
        from .services.push_service import PushService
        from .services.log_service import LogService
        from .services.audit_service import AuditService
        from .services.cache_service import CacheService
        from .services.config_service import ConfigService
        
        self.email_service = EmailService()
        self.sms_service = SMSService()
        self.push_service = PushService()
        self.log_service = LogService()
        self.audit_service = AuditService()
        self.cache_service = CacheService()
        self.config_service = ConfigService()
    
    def process_notification(self, message, user):
        """Method that uses too many dependencies."""
        self.log_service.log(f"Processing notification for {user}")
        self.audit_service.audit("notification_sent", user)
        
        config = self.config_service.get_config()
        cached_data = self.cache_service.get(f"user_{user}")
        
        if config['email_enabled']:
            self.email_service.send(message, user)
        
        if config['sms_enabled']:
            self.sms_service.send(message, user)
        
        if config['push_enabled']:
            self.push_service.send(message, user)

class LowCohesionClass:
    """Class with low cohesion - does unrelated things."""
    
    def calculate_tax(self, amount):
        """Tax calculation."""
        return amount * 0.1
    
    def send_email(self, recipient, message):
        """Email sending."""
        print(f"Sending email to {recipient}: {message}")
    
    def format_date(self, date):
        """Date formatting."""
        return date.strftime("%Y-%m-%d")
    
    def validate_credit_card(self, card_number):
        """Credit card validation."""
        return len(card_number) == 16
    
    def generate_report(self, data):
        """Report generation."""
        return f"Report: {len(data)} items"
''')
    
    print(f"Created sample project at: {temp_dir}")
    return temp_dir


def demonstrate_ai_analysis():
    """Demonstrate the AI analysis engine capabilities."""
    print("🤖 AI-Powered Code Analysis Engine Demo")
    print("=" * 50)
    
    # Create sample project
    print("\n📁 Creating sample project with various code issues...")
    project_path = create_sample_project()
    
    try:
        # Initialize indexing engine
        print("\n🔍 Initializing indexing engine...")
        indexing_engine = IndexingEngine(project_path)
        
        # Build index
        print("📊 Building code index...")
        indexing_engine.build_index()
        
        # Initialize AI service (optional - will work without it)
        print("🧠 Initializing AI service...")
        try:
            ai_service = AzureOpenAIService()
        except Exception as e:
            print(f"⚠️  AI service not available: {e}")
            print("📝 Continuing with static analysis only...")
            ai_service = None
        
        # Initialize AI analysis engine
        print("🔧 Initializing AI analysis engine...")
        ai_engine = AIAnalysisEngine(indexing_engine, ai_service)
        
        # Perform comprehensive analysis
        print("\n🔬 Performing comprehensive code analysis...")
        print("   This may take a moment...")
        
        result = ai_engine.analyze_comprehensive(project_path)
        
        # Display results
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE ANALYSIS RESULTS")
        print("=" * 60)
        
        print(f"\n🏥 Overall Health Score: {result.overall_health_score:.2f}/1.0")
        
        # Quality Analysis
        print(f"\n📈 Code Quality Analysis:")
        print(f"   Score: {result.quality_analysis.overall_score:.2f}/1.0")
        print(f"   Issues Found: {len(result.quality_analysis.code_smells)}")
        print(f"   Maintainability Index: {result.quality_analysis.maintainability_index:.2f}")
        print(f"   Test Coverage Estimate: {result.quality_analysis.test_coverage_estimate:.1%}")
        print(f"   Documentation Coverage: {result.quality_analysis.documentation_coverage:.1%}")
        
        if result.quality_analysis.code_smells:
            print(f"\n   🔍 Top Quality Issues:")
            for i, smell in enumerate(result.quality_analysis.code_smells[:3], 1):
                print(f"      {i}. {smell.name} ({smell.severity}) - {smell.description}")
        
        # Security Analysis
        print(f"\n🔒 Security Analysis:")
        print(f"   Score: {result.security_analysis.overall_security_score:.2f}/1.0")
        print(f"   Vulnerabilities Found: {len(result.security_analysis.security_issues)}")
        
        if result.security_analysis.security_issues:
            print(f"\n   ⚠️  Top Security Issues:")
            for i, issue in enumerate(result.security_analysis.security_issues[:3], 1):
                print(f"      {i}. {issue.vulnerability_type} ({issue.severity}) - {issue.description}")
        
        # Performance Analysis
        print(f"\n⚡ Performance Analysis:")
        print(f"   Score: {result.performance_analysis.overall_performance_score:.2f}/1.0")
        print(f"   Performance Issues: {len(result.performance_analysis.performance_issues)}")
        
        if result.performance_analysis.performance_issues:
            print(f"\n   🐌 Top Performance Issues:")
            for i, issue in enumerate(result.performance_analysis.performance_issues[:3], 1):
                print(f"      {i}. {issue.issue_type} ({issue.impact}) - {issue.description}")
        
        # Architectural Analysis
        print(f"\n🏗️  Architectural Analysis:")
        print(f"   Score: {result.architectural_analysis.overall_architecture_score:.2f}/1.0")
        print(f"   Violations Found: {len(result.architectural_analysis.violations)}")
        
        if result.architectural_analysis.violations:
            print(f"\n   🚫 Top Architectural Violations:")
            for i, violation in enumerate(result.architectural_analysis.violations[:3], 1):
                print(f"      {i}. {violation.rule_name} ({violation.severity}) - {violation.description}")
        
        # Critical Issues
        if result.critical_issues:
            print(f"\n🚨 Critical Issues Requiring Immediate Attention:")
            for i, issue in enumerate(result.critical_issues, 1):
                print(f"   {i}. {issue}")
        
        # Priority Recommendations
        if result.priority_recommendations:
            print(f"\n💡 Priority Recommendations:")
            for i, rec in enumerate(result.priority_recommendations, 1):
                print(f"   {i}. {rec}")
        
        # Analysis Summary
        print(f"\n📋 Analysis Summary:")
        print(f"   • Analysis Duration: {result.analysis_duration:.2f} seconds")
        print(f"   • Analysis Timestamp: {result.analysis_timestamp}")
        
        print(f"\n✅ Analysis complete! Check the detailed results above.")
        
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        import shutil
        try:
            shutil.rmtree(project_path)
            print(f"\n🧹 Cleaned up temporary project at {project_path}")
        except Exception as e:
            print(f"⚠️  Could not clean up {project_path}: {e}")


if __name__ == "__main__":
    demonstrate_ai_analysis()