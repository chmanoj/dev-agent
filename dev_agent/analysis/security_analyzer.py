"""Security analyzer for identifying vulnerabilities and security issues."""

from __future__ import annotations

import ast
import logging
import re
from collections import Counter
from pathlib import Path
from typing import Any

from ..interfaces.ai_analysis_interface import ISecurityAnalyzer
from ..interfaces.indexing_interface import IIndexingEngine
from ..models.analysis import SecurityAnalysisResult, SecurityIssue
from ..services.azure_openai_service import AzureOpenAIService, ChatMessage

logger = logging.getLogger(__name__)


class SecurityAnalyzer(ISecurityAnalyzer):
    """Analyzer for security vulnerabilities and issues."""

    def __init__(
        self,
        indexing_engine: IIndexingEngine,
        ai_service: AzureOpenAIService | None = None,
    ):
        """Initialize the security analyzer.

        Args:
            indexing_engine: The indexing engine with parsed codebase data
            ai_service: AI service for enhanced analysis (optional)
        """
        self.indexing_engine = indexing_engine
        self.ai_service = ai_service
        self.ast_index = getattr(indexing_engine, "ast_index", None)

        # Security patterns and rules
        self._init_security_patterns()

    def analyze(self, project_path: str) -> SecurityAnalysisResult:
        """Perform comprehensive security analysis of the project.

        Args:
            project_path: Path to the project directory

        Returns:
            Security analysis results
        """
        logger.info(f"Analyzing security for {project_path}")

        if not self.ast_index:
            logger.warning("No AST index available for security analysis")
            return self._create_empty_result()

        # Analyze security issues
        security_issues = self._analyze_all_security_issues(project_path)

        # Calculate metrics
        overall_security_score = self._calculate_security_score(security_issues)
        vulnerability_counts = self._count_vulnerabilities_by_severity(security_issues)
        security_hotspots = self._identify_security_hotspots(security_issues)
        compliance_issues = self._check_compliance_issues(project_path)

        # Generate summary and recommendations
        summary = self._generate_security_summary(security_issues, overall_security_score)
        recommendations = self._generate_security_recommendations(security_issues, compliance_issues)

        return SecurityAnalysisResult(
            overall_security_score=overall_security_score,
            security_issues=security_issues,
            vulnerability_count_by_severity=vulnerability_counts,
            security_hotspots=security_hotspots,
            compliance_issues=compliance_issues,
            summary=summary,
            recommendations=recommendations,
        )

    def scan_vulnerabilities(self, code: str, file_path: str) -> list[SecurityIssue]:
        """Scan for security vulnerabilities in the given code.

        Args:
            code: Source code to analyze
            file_path: Path to the file being analyzed

        Returns:
            List of identified security issues
        """
        issues = []

        try:
            tree = ast.parse(code)
            lines = code.split('\n')

            # Scan for different types of vulnerabilities
            issues.extend(self._scan_injection_vulnerabilities(tree, file_path, lines))
            issues.extend(self._scan_authentication_issues(tree, file_path, lines))
            issues.extend(self._scan_authorization_issues(tree, file_path, lines))
            issues.extend(self._scan_data_exposure_issues(tree, file_path, lines))
            issues.extend(self._scan_cryptographic_issues(tree, file_path, lines))
            issues.extend(self._scan_input_validation_issues(tree, file_path, lines))
            issues.extend(self._scan_configuration_issues(code, file_path, lines))
            issues.extend(self._scan_dependency_vulnerabilities(tree, file_path, lines))

        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")

        return issues

    def check_input_validation(self, code: str) -> list[SecurityIssue]:
        """Check for input validation issues.

        Args:
            code: Source code to analyze

        Returns:
            List of input validation security issues
        """
        issues = []
        lines = code.split('\n')

        try:
            tree = ast.parse(code)
            
            # Look for direct use of user input without validation
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # Check for dangerous functions with user input
                    if (isinstance(node.func, ast.Name) and 
                        node.func.id in ['eval', 'exec', 'compile']):
                        issues.append(
                            SecurityIssue(
                                vulnerability_type="Code Injection",
                                description=f"Use of dangerous function '{node.func.id}' detected",
                                file_path="<analyzed_code>",
                                line_number=node.lineno,
                                severity="critical",
                                cwe_id="CWE-94",
                                suggestion="Avoid using eval/exec with user input. Use safer alternatives.",
                                code_snippet=self._extract_code_snippet(lines, node.lineno, 1),
                                confidence=0.9,
                            )
                        )

        except SyntaxError:
            pass

        return issues

    def analyze_authentication(self, project_path: str) -> list[SecurityIssue]:
        """Analyze authentication and authorization patterns.

        Args:
            project_path: Path to the project directory

        Returns:
            List of authentication/authorization security issues
        """
        issues = []

        if not self.ast_index:
            return issues

        # Look for authentication-related code
        auth_functions = []
        for func_def in self.ast_index.functions.values():
            if any(keyword in func_def.name.lower() 
                   for keyword in ['auth', 'login', 'password', 'token', 'session']):
                auth_functions.append(func_def)

        # Analyze authentication functions for common issues
        for func_def in auth_functions:
            try:
                with open(func_def.file_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                    issues.extend(self._analyze_auth_function(func_def, code))
            except Exception as e:
                logger.warning(f"Error analyzing auth function {func_def.name}: {e}")

        return issues

    def check_data_exposure(self, code: str) -> list[SecurityIssue]:
        """Check for potential data exposure issues.

        Args:
            code: Source code to analyze

        Returns:
            List of data exposure security issues
        """
        issues = []
        lines = code.split('\n')

        # Check for hardcoded secrets
        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded Password"),
            (r'api_key\s*=\s*["\'][^"\']+["\']', "Hardcoded API Key"),
            (r'secret\s*=\s*["\'][^"\']+["\']', "Hardcoded Secret"),
            (r'token\s*=\s*["\'][^"\']+["\']', "Hardcoded Token"),
        ]

        for i, line in enumerate(lines, 1):
            for pattern, issue_type in secret_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(
                        SecurityIssue(
                            vulnerability_type="Information Exposure",
                            description=f"{issue_type} found in source code",
                            file_path="<analyzed_code>",
                            line_number=i,
                            severity="high",
                            cwe_id="CWE-798",
                            suggestion="Use environment variables or secure configuration for secrets",
                            code_snippet=line.strip(),
                            confidence=0.8,
                        )
                    )

        return issues

    def _init_security_patterns(self) -> None:
        """Initialize security patterns and rules."""
        self.dangerous_functions = {
            'eval': 'CWE-94',
            'exec': 'CWE-94',
            'compile': 'CWE-94',
            'input': 'CWE-20',
            'raw_input': 'CWE-20',
        }

        self.sql_injection_patterns = [
            r'execute\s*\(\s*["\'].*%.*["\']',
            r'cursor\.execute\s*\(\s*["\'].*\+.*["\']',
            r'query\s*=\s*["\'].*%.*["\']',
        ]

        self.xss_patterns = [
            r'render_template_string\s*\(',
            r'Markup\s*\(',
            r'safe\s*\|',
        ]

        self.crypto_weak_patterns = [
            r'md5\s*\(',
            r'sha1\s*\(',
            r'DES\s*\(',
            r'RC4\s*\(',
        ]

    def _analyze_all_security_issues(self, project_path: str) -> list[SecurityIssue]:
        """Analyze security issues across all files in the project."""
        all_issues = []

        if not self.ast_index:
            return all_issues

        # Analyze each Python file
        for file_path, metadata in self.ast_index.file_metadata.items():
            if file_path.endswith('.py'):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        code = f.read()
                        file_issues = self.scan_vulnerabilities(code, file_path)
                        all_issues.extend(file_issues)
                except Exception as e:
                    logger.warning(f"Error analyzing {file_path}: {e}")

        return all_issues

    def _scan_injection_vulnerabilities(
        self, tree: ast.AST, file_path: str, lines: list[str]
    ) -> list[SecurityIssue]:
        """Scan for injection vulnerabilities."""
        issues = []

        for node in ast.walk(tree):
            # SQL Injection - check for string formatting with % operator
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
                # Check if left side looks like SQL and right side is variable
                if isinstance(node.left, ast.Str) and any(keyword in node.left.s.upper() 
                                                         for keyword in ['SELECT', 'INSERT', 'UPDATE', 'DELETE']):
                    issues.append(
                        SecurityIssue(
                            vulnerability_type="SQL Injection",
                            description="Potential SQL injection via string formatting",
                            file_path=file_path,
                            line_number=node.lineno,
                            severity="high",
                            cwe_id="CWE-89",
                            suggestion="Use parameterized queries instead of string formatting",
                            code_snippet=self._extract_code_snippet(lines, node.lineno, 1),
                            confidence=0.8,
                        )
                    )
            
            # SQL Injection in execute calls
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr == 'execute':
                    # Check if SQL query is constructed with string formatting
                    for arg in node.args:
                        if isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Mod):
                            issues.append(
                                SecurityIssue(
                                    vulnerability_type="SQL Injection",
                                    description="Potential SQL injection via string formatting in execute call",
                                    file_path=file_path,
                                    line_number=node.lineno,
                                    severity="high",
                                    cwe_id="CWE-89",
                                    suggestion="Use parameterized queries instead of string formatting",
                                    code_snippet=self._extract_code_snippet(lines, node.lineno, 1),
                                    confidence=0.8,
                                )
                            )

            # Command Injection
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in ['os.system', 'subprocess.call', 'subprocess.run']:
                    # Check if command includes user input
                    issues.append(
                        SecurityIssue(
                            vulnerability_type="Command Injection",
                            description=f"Potential command injection via {node.func.id}",
                            file_path=file_path,
                            line_number=node.lineno,
                            severity="high",
                            cwe_id="CWE-78",
                            suggestion="Validate and sanitize input, use subprocess with shell=False",
                            code_snippet=self._extract_code_snippet(lines, node.lineno, 1),
                            confidence=0.7,
                        )
                    )

        return issues

    def _scan_authentication_issues(
        self, tree: ast.AST, file_path: str, lines: list[str]
    ) -> list[SecurityIssue]:
        """Scan for authentication-related issues."""
        issues = []

        for node in ast.walk(tree):
            # Weak password hashing
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in ['md5', 'sha1']:
                    issues.append(
                        SecurityIssue(
                            vulnerability_type="Weak Cryptography",
                            description=f"Use of weak hash function: {node.func.id}",
                            file_path=file_path,
                            line_number=node.lineno,
                            severity="medium",
                            cwe_id="CWE-327",
                            suggestion="Use stronger hash functions like SHA-256 or bcrypt for passwords",
                            code_snippet=self._extract_code_snippet(lines, node.lineno, 1),
                            confidence=0.9,
                        )
                    )

        return issues

    def _scan_authorization_issues(
        self, tree: ast.AST, file_path: str, lines: list[str]
    ) -> list[SecurityIssue]:
        """Scan for authorization-related issues."""
        issues = []

        # Look for missing authorization checks
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if function handles sensitive operations without auth checks
                if any(keyword in node.name.lower() 
                       for keyword in ['delete', 'admin', 'modify', 'update']):
                    # Simple heuristic: look for auth-related code in function
                    has_auth_check = False
                    for child in ast.walk(node):
                        if isinstance(child, ast.Name) and any(
                            auth_keyword in child.id.lower()
                            for auth_keyword in ['auth', 'permission', 'role', 'user']
                        ):
                            has_auth_check = True
                            break

                    if not has_auth_check:
                        issues.append(
                            SecurityIssue(
                                vulnerability_type="Missing Authorization",
                                description=f"Function '{node.name}' may lack authorization checks",
                                file_path=file_path,
                                line_number=node.lineno,
                                severity="medium",
                                cwe_id="CWE-862",
                                suggestion="Add proper authorization checks for sensitive operations",
                                code_snippet=self._extract_code_snippet(lines, node.lineno, 3),
                                confidence=0.6,
                            )
                        )

        return issues

    def _scan_data_exposure_issues(
        self, tree: ast.AST, file_path: str, lines: list[str]
    ) -> list[SecurityIssue]:
        """Scan for data exposure issues."""
        issues = []

        # Check for logging sensitive data
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check logging calls
                if (isinstance(node.func, ast.Attribute) and 
                    node.func.attr in ['info', 'debug', 'warning', 'error']):
                    for arg in node.args:
                        if isinstance(arg, ast.Str):
                            # Check if log message contains sensitive keywords
                            if any(keyword in arg.s.lower() 
                                   for keyword in ['password', 'token', 'key', 'secret']):
                                issues.append(
                                    SecurityIssue(
                                        vulnerability_type="Information Exposure",
                                        description="Potential logging of sensitive information",
                                        file_path=file_path,
                                        line_number=node.lineno,
                                        severity="medium",
                                        cwe_id="CWE-532",
                                        suggestion="Avoid logging sensitive information",
                                        code_snippet=self._extract_code_snippet(lines, node.lineno, 1),
                                        confidence=0.7,
                                    )
                                )

        return issues

    def _scan_cryptographic_issues(
        self, tree: ast.AST, file_path: str, lines: list[str]
    ) -> list[SecurityIssue]:
        """Scan for cryptographic issues."""
        issues = []

        for node in ast.walk(tree):
            # Check for weak random number generation
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if (node.func.attr == 'random' and 
                    isinstance(node.func.value, ast.Name) and 
                    node.func.value.id == 'random'):
                    issues.append(
                        SecurityIssue(
                            vulnerability_type="Weak Random Number Generation",
                            description="Use of predictable random number generator",
                            file_path=file_path,
                            line_number=node.lineno,
                            severity="medium",
                            cwe_id="CWE-338",
                            suggestion="Use secrets module for cryptographically secure random numbers",
                            code_snippet=self._extract_code_snippet(lines, node.lineno, 1),
                            confidence=0.8,
                        )
                    )

        return issues

    def _scan_input_validation_issues(
        self, tree: ast.AST, file_path: str, lines: list[str]
    ) -> list[SecurityIssue]:
        """Scan for input validation issues."""
        issues = []

        for node in ast.walk(tree):
            # Check for dangerous functions
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in self.dangerous_functions:
                    cwe_id = self.dangerous_functions[node.func.id]
                    issues.append(
                        SecurityIssue(
                            vulnerability_type="Code Injection",
                            description=f"Use of dangerous function: {node.func.id}",
                            file_path=file_path,
                            line_number=node.lineno,
                            severity="critical",
                            cwe_id=cwe_id,
                            suggestion=f"Avoid using {node.func.id} with user input",
                            code_snippet=self._extract_code_snippet(lines, node.lineno, 1),
                            confidence=0.9,
                        )
                    )

        return issues

    def _scan_configuration_issues(
        self, code: str, file_path: str, lines: list[str]
    ) -> list[SecurityIssue]:
        """Scan for configuration-related security issues."""
        issues = []

        # Check for hardcoded secrets
        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']{8,}["\']', "Hardcoded Password", "CWE-798"),
            (r'api_key\s*=\s*["\'][^"\']{16,}["\']', "Hardcoded API Key", "CWE-798"),
            (r'secret\s*=\s*["\'][^"\']{16,}["\']', "Hardcoded Secret", "CWE-798"),
            (r'token\s*=\s*["\'][^"\']{16,}["\']', "Hardcoded Token", "CWE-798"),
        ]

        for i, line in enumerate(lines, 1):
            for pattern, issue_type, cwe_id in secret_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(
                        SecurityIssue(
                            vulnerability_type="Information Exposure",
                            description=f"{issue_type} found in source code",
                            file_path=file_path,
                            line_number=i,
                            severity="high",
                            cwe_id=cwe_id,
                            suggestion="Use environment variables or secure configuration for secrets",
                            code_snippet=line.strip(),
                            confidence=0.8,
                        )
                    )

        return issues

    def _scan_dependency_vulnerabilities(
        self, tree: ast.AST, file_path: str, lines: list[str]
    ) -> list[SecurityIssue]:
        """Scan for dependency-related vulnerabilities."""
        issues = []

        # This would typically integrate with vulnerability databases
        # For now, we'll check for known problematic imports
        vulnerable_imports = {
            'pickle': 'Pickle module can execute arbitrary code during deserialization',
            'yaml': 'PyYAML unsafe loading can execute arbitrary code',
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in vulnerable_imports:
                        issues.append(
                            SecurityIssue(
                                vulnerability_type="Insecure Deserialization",
                                description=vulnerable_imports[alias.name],
                                file_path=file_path,
                                line_number=node.lineno,
                                severity="medium",
                                cwe_id="CWE-502",
                                suggestion=f"Use safer alternatives to {alias.name} or ensure safe usage",
                                code_snippet=self._extract_code_snippet(lines, node.lineno, 1),
                                confidence=0.6,
                            )
                        )

        return issues

    def _analyze_auth_function(self, func_def: Any, code: str) -> list[SecurityIssue]:
        """Analyze an authentication function for security issues."""
        issues = []
        lines = code.split('\n')

        try:
            tree = ast.parse(code)
            
            # Find the specific function
            for node in ast.walk(tree):
                if (isinstance(node, ast.FunctionDef) and 
                    node.name == func_def.name):
                    
                    # Check for password comparison issues
                    for child in ast.walk(node):
                        if isinstance(child, ast.Compare):
                            # Look for direct password comparison
                            issues.append(
                                SecurityIssue(
                                    vulnerability_type="Weak Authentication",
                                    description="Potential timing attack vulnerability in password comparison",
                                    file_path=func_def.file_path,
                                    line_number=child.lineno,
                                    severity="medium",
                                    cwe_id="CWE-208",
                                    suggestion="Use constant-time comparison for passwords",
                                    code_snippet=self._extract_code_snippet(lines, child.lineno, 1),
                                    confidence=0.5,
                                )
                            )
                    break

        except Exception as e:
            logger.warning(f"Error analyzing auth function: {e}")

        return issues

    def _calculate_security_score(self, security_issues: list[SecurityIssue]) -> float:
        """Calculate overall security score based on issues found."""
        if not security_issues:
            return 1.0

        # Weight issues by severity
        severity_weights = {
            "critical": 1.0,
            "high": 0.7,
            "medium": 0.4,
            "low": 0.1,
        }

        total_penalty = 0.0
        for issue in security_issues:
            weight = severity_weights.get(issue.severity, 0.1)
            confidence_factor = issue.confidence
            total_penalty += weight * confidence_factor

        # Normalize score (assuming max 10 critical issues would give score 0)
        max_penalty = 10.0
        score = max(0.0, 1.0 - (total_penalty / max_penalty))
        
        return score

    def _count_vulnerabilities_by_severity(
        self, security_issues: list[SecurityIssue]
    ) -> dict[str, int]:
        """Count vulnerabilities by severity level."""
        return dict(Counter(issue.severity for issue in security_issues))

    def _identify_security_hotspots(self, security_issues: list[SecurityIssue]) -> list[str]:
        """Identify files with the most security issues."""
        file_issue_counts = Counter(issue.file_path for issue in security_issues)
        
        # Return top 5 files with most issues
        hotspots = []
        for file_path, count in file_issue_counts.most_common(5):
            hotspots.append(f"{Path(file_path).name}: {count} issues")
        
        return hotspots

    def _check_compliance_issues(self, project_path: str) -> list[str]:
        """Check for compliance-related issues."""
        compliance_issues = []

        # Check for missing security headers (if web app)
        # Check for missing input validation
        # Check for missing error handling
        # This would be expanded based on specific compliance requirements

        return compliance_issues

    def _generate_security_summary(
        self, security_issues: list[SecurityIssue], overall_score: float
    ) -> str:
        """Generate a summary of the security analysis."""
        severity_counts = Counter(issue.severity for issue in security_issues)
        
        summary = f"Overall security score: {overall_score:.2f}/1.0. "
        summary += f"Found {len(security_issues)} security issues: "
        
        if severity_counts:
            parts = []
            for severity in ["critical", "high", "medium", "low"]:
                if severity_counts[severity] > 0:
                    parts.append(f"{severity_counts[severity]} {severity}")
            summary += ", ".join(parts) + "."
        else:
            summary += "No significant security issues found."
            
        return summary

    def _generate_security_recommendations(
        self, security_issues: list[SecurityIssue], compliance_issues: list[str]
    ) -> list[str]:
        """Generate security improvement recommendations."""
        recommendations = []
        
        # Critical and high severity issues
        critical_high = [i for i in security_issues if i.severity in ["critical", "high"]]
        if critical_high:
            recommendations.append(f"Immediately address {len(critical_high)} critical/high severity security issues")
        
        # Common vulnerability types
        vuln_types = Counter(issue.vulnerability_type for issue in security_issues)
        for vuln_type, count in vuln_types.most_common(3):
            if count > 2:
                recommendations.append(f"Address {count} instances of '{vuln_type}' vulnerabilities")
        
        # Compliance issues
        if compliance_issues:
            recommendations.append("Address compliance issues to meet security standards")
        
        # General recommendations
        if any(issue.cwe_id == "CWE-798" for issue in security_issues):
            recommendations.append("Remove hardcoded secrets and use secure configuration management")
        
        if any(issue.cwe_id in ["CWE-89", "CWE-78", "CWE-94"] for issue in security_issues):
            recommendations.append("Implement proper input validation and sanitization")
        
        return recommendations[:5]

    def _extract_code_snippet(self, lines: list[str], line_number: int, context: int = 1) -> str:
        """Extract a code snippet around the specified line."""
        start_idx = max(0, line_number - context - 1)
        end_idx = min(len(lines), line_number + context)
        return '\n'.join(lines[start_idx:end_idx])

    def _create_empty_result(self) -> SecurityAnalysisResult:
        """Create an empty security analysis result."""
        return SecurityAnalysisResult(
            overall_security_score=0.0,
            security_issues=[],
            vulnerability_count_by_severity={},
            security_hotspots=[],
            compliance_issues=[],
            summary="No security analysis available - missing AST index",
            recommendations=["Ensure project is properly indexed before security analysis"],
        )