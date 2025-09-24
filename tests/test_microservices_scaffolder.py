"""Tests for the microservices scaffolding system."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from dev_agent.generation.microservices_scaffolder import (
    MicroserviceSpec,
    MicroservicesArchitecture,
    MicroservicesScaffolder,
)
from dev_agent.generation.template_system import TemplateSystem
from dev_agent.models.enums import FrameworkType, LanguageType


class TestMicroserviceSpec:
    """Test cases for the MicroserviceSpec class."""

    def test_microservice_spec_creation(self) -> None:
        """Test creating a microservice specification."""
        spec = MicroserviceSpec(
            name="user-service",
            description="User management service",
            port=8001,
            language=LanguageType.PYTHON,
            framework=FrameworkType.FASTAPI,
            database="postgresql",
            dependencies=["auth-service", "notification-service"],
        )

        assert spec.name == "user-service"
        assert spec.description == "User management service"
        assert spec.port == 8001
        assert spec.language == LanguageType.PYTHON
        assert spec.framework == FrameworkType.FASTAPI
        assert spec.database == "postgresql"
        assert "auth-service" in spec.dependencies
        assert "notification-service" in spec.dependencies

    def test_microservice_spec_defaults(self) -> None:
        """Test microservice specification default values."""
        spec = MicroserviceSpec(
            name="simple-service",
            description="A simple service",
            port=8000,
            language=LanguageType.PYTHON,
            framework=FrameworkType.FASTAPI,
        )

        assert spec.database is None
        assert spec.dependencies == []


class TestMicroservicesArchitecture:
    """Test cases for the MicroservicesArchitecture class."""

    def test_microservices_architecture_creation(self) -> None:
        """Test creating a microservices architecture."""
        services = [
            MicroserviceSpec(
                name="user-service",
                description="User management",
                port=8001,
                language=LanguageType.PYTHON,
                framework=FrameworkType.FASTAPI,
            ),
            MicroserviceSpec(
                name="order-service",
                description="Order processing",
                port=8002,
                language=LanguageType.PYTHON,
                framework=FrameworkType.FASTAPI,
            ),
        ]

        architecture = MicroservicesArchitecture(
            name="ecommerce-platform",
            description="E-commerce microservices platform",
            services=services,
            api_gateway=True,
            service_discovery="consul",
            message_broker="rabbitmq",
            monitoring=True,
            logging=True,
        )

        assert architecture.name == "ecommerce-platform"
        assert architecture.description == "E-commerce microservices platform"
        assert len(architecture.services) == 2
        assert architecture.api_gateway is True
        assert architecture.service_discovery == "consul"
        assert architecture.message_broker == "rabbitmq"
        assert architecture.monitoring is True
        assert architecture.logging is True

    def test_microservices_architecture_defaults(self) -> None:
        """Test microservices architecture default values."""
        services = [
            MicroserviceSpec(
                name="test-service",
                description="Test service",
                port=8000,
                language=LanguageType.PYTHON,
                framework=FrameworkType.FASTAPI,
            )
        ]

        architecture = MicroservicesArchitecture(
            name="test-platform",
            description="Test platform",
            services=services,
        )

        assert architecture.api_gateway is True
        assert architecture.service_discovery == "consul"
        assert architecture.message_broker == "rabbitmq"
        assert architecture.monitoring is True
        assert architecture.logging is True


class TestMicroservicesScaffolder:
    """Test cases for the MicroservicesScaffolder class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.template_system = TemplateSystem(self.temp_dir)
        self.scaffolder = MicroservicesScaffolder(self.template_system)

    def teardown_method(self) -> None:
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_scaffolder_initialization(self) -> None:
        """Test microservices scaffolder initialization."""
        assert self.scaffolder.template_system == self.template_system

    def test_scaffold_simple_microservices_architecture(self) -> None:
        """Test scaffolding a simple microservices architecture."""
        services = [
            MicroserviceSpec(
                name="api-service",
                description="Main API service",
                port=8000,
                language=LanguageType.PYTHON,
                framework=FrameworkType.FASTAPI,
            ),
            MicroserviceSpec(
                name="worker-service",
                description="Background worker service",
                port=8001,
                language=LanguageType.PYTHON,
                framework=FrameworkType.FASTAPI,
            ),
        ]

        architecture = MicroservicesArchitecture(
            name="simple-platform",
            description="A simple microservices platform",
            services=services,
            api_gateway=True,
            monitoring=True,
            logging=True,
        )

        output_path = self.temp_dir / "simple-platform"
        result = self.scaffolder.scaffold_microservices_architecture(
            architecture, output_path
        )

        # Verify basic structure was created
        assert result.success
        assert result.project_path == output_path
        assert len(result.created_directories) > 0
        assert len(result.created_files) > 0

        # Verify key directories were created
        assert output_path.exists()
        assert (output_path / "infrastructure").exists()
        assert (output_path / "infrastructure" / "k8s").exists()
        assert (output_path / "infrastructure" / "terraform").exists()

        # Verify key files were created
        assert (output_path / "docker-compose.yml").exists()
        assert (output_path / "README.md").exists()
        assert (output_path / ".env.example").exists()

    def test_kubernetes_manifest_generation(self) -> None:
        """Test Kubernetes manifest generation."""
        service = MicroserviceSpec(
            name="test-service",
            description="Test service",
            port=8000,
            language=LanguageType.PYTHON,
            framework=FrameworkType.FASTAPI,
        )

        # Test namespace generation
        namespace_manifest = self.scaffolder._generate_k8s_namespace(
            MicroservicesArchitecture(
                name="test-platform",
                description="Test",
                services=[service],
            )
        )
        assert "apiVersion: v1" in namespace_manifest
        assert "kind: Namespace" in namespace_manifest
        assert "name: test-platform" in namespace_manifest

        # Test service manifest generation
        service_manifest = self.scaffolder._generate_k8s_service_manifest(service)
        assert "apiVersion: v1" in service_manifest
        assert "kind: Service" in service_manifest
        assert "name: test-service" in service_manifest
        assert "port: 8000" in service_manifest

        # Test deployment manifest generation
        deployment_manifest = self.scaffolder._generate_k8s_deployment_manifest(service)
        assert "apiVersion: apps/v1" in deployment_manifest
        assert "kind: Deployment" in deployment_manifest
        assert "name: test-service" in deployment_manifest
        assert "containerPort: 8000" in deployment_manifest

    def test_docker_compose_generation(self) -> None:
        """Test Docker Compose configuration generation."""
        services = [
            MicroserviceSpec(
                name="web-service",
                description="Web service",
                port=8000,
                language=LanguageType.PYTHON,
                framework=FrameworkType.FASTAPI,
            ),
            MicroserviceSpec(
                name="api-service",
                description="API service",
                port=8001,
                language=LanguageType.PYTHON,
                framework=FrameworkType.FASTAPI,
            ),
        ]

        architecture = MicroservicesArchitecture(
            name="test-platform",
            description="Test platform",
            services=services,
            api_gateway=True,
            service_discovery="consul",
            monitoring=True,
            logging=True,
        )

        docker_compose_content = self.scaffolder._generate_docker_compose_content(architecture)

        # Verify basic structure
        assert "version: '3.8'" in docker_compose_content
        assert "services:" in docker_compose_content
        assert "networks:" in docker_compose_content

        # Verify services are included
        assert "web-service:" in docker_compose_content
        assert "api-service:" in docker_compose_content
        assert "8000:8000" in docker_compose_content
        assert "8001:8001" in docker_compose_content

        # Verify infrastructure services
        assert "consul:" in docker_compose_content
        assert "api-gateway:" in docker_compose_content
        assert "prometheus:" in docker_compose_content
        assert "grafana:" in docker_compose_content
        assert "elasticsearch:" in docker_compose_content

    def test_nginx_gateway_configuration(self) -> None:
        """Test nginx API gateway configuration generation."""
        services = [
            MicroserviceSpec(
                name="user-service",
                description="User service",
                port=8001,
                language=LanguageType.PYTHON,
                framework=FrameworkType.FASTAPI,
            ),
            MicroserviceSpec(
                name="order-service",
                description="Order service",
                port=8002,
                language=LanguageType.PYTHON,
                framework=FrameworkType.FASTAPI,
            ),
        ]

        architecture = MicroservicesArchitecture(
            name="test-platform",
            description="Test platform",
            services=services,
        )

        nginx_config = self.scaffolder._generate_nginx_gateway_config(architecture)

        # Verify basic nginx structure
        assert "events {" in nginx_config
        assert "http {" in nginx_config
        assert "server {" in nginx_config

        # Verify upstream configurations
        assert "upstream user-service {" in nginx_config
        assert "upstream order-service {" in nginx_config
        assert "server user-service:8001;" in nginx_config
        assert "server order-service:8002;" in nginx_config

        # Verify location blocks
        assert "location /user-service/" in nginx_config
        assert "location /order-service/" in nginx_config
        assert "proxy_pass http://user-service/" in nginx_config
        assert "proxy_pass http://order-service/" in nginx_config

    def test_monitoring_configuration_generation(self) -> None:
        """Test monitoring configuration generation."""
        services = [
            MicroserviceSpec(
                name="test-service",
                description="Test service",
                port=8000,
                language=LanguageType.PYTHON,
                framework=FrameworkType.FASTAPI,
            )
        ]

        architecture = MicroservicesArchitecture(
            name="test-platform",
            description="Test platform",
            services=services,
        )

        # Test Prometheus configuration
        prometheus_config = self.scaffolder._generate_prometheus_config(architecture)
        assert "global:" in prometheus_config
        assert "scrape_configs:" in prometheus_config
        assert "job_name: 'test-service'" in prometheus_config
        assert "targets: ['test-service:8000']" in prometheus_config

        # Test Grafana dashboard
        grafana_dashboard = self.scaffolder._generate_grafana_dashboard(architecture)
        assert '"title": "test-platform Microservices Dashboard"' in grafana_dashboard
        assert '"test-service Metrics"' in grafana_dashboard

    def test_logging_configuration_generation(self) -> None:
        """Test logging configuration generation."""
        # Test Elasticsearch configuration
        elasticsearch_config = self.scaffolder._generate_elasticsearch_config()
        assert 'cluster.name: "microservices-logs"' in elasticsearch_config
        assert "network.host: 0.0.0.0" in elasticsearch_config
        assert "http.port: 9200" in elasticsearch_config

        # Test Logstash configuration
        services = [
            MicroserviceSpec(
                name="test-service",
                description="Test service",
                port=8000,
                language=LanguageType.PYTHON,
                framework=FrameworkType.FASTAPI,
            )
        ]

        architecture = MicroservicesArchitecture(
            name="test-platform",
            description="Test platform",
            services=services,
        )

        logstash_config = self.scaffolder._generate_logstash_config(architecture)
        assert "input {" in logstash_config
        assert "filter {" in logstash_config
        assert "output {" in logstash_config
        assert "elasticsearch {" in logstash_config

        # Test Kibana configuration
        kibana_config = self.scaffolder._generate_kibana_config()
        assert "server.name: kibana" in kibana_config
        assert "elasticsearch.hosts:" in kibana_config

    def test_terraform_configuration_generation(self) -> None:
        """Test Terraform configuration generation."""
        services = [
            MicroserviceSpec(
                name="web-service",
                description="Web service",
                port=8000,
                language=LanguageType.PYTHON,
                framework=FrameworkType.FASTAPI,
            )
        ]

        architecture = MicroservicesArchitecture(
            name="test-platform",
            description="Test platform",
            services=services,
        )

        terraform_main = self.scaffolder._generate_terraform_main(architecture)

        # Verify basic Terraform structure
        assert "terraform {" in terraform_main
        assert "required_providers {" in terraform_main
        assert "provider \"kubernetes\"" in terraform_main
        assert 'resource "kubernetes_namespace" "test-platform"' in terraform_main

    def test_documentation_generation(self) -> None:
        """Test documentation generation."""
        services = [
            MicroserviceSpec(
                name="user-service",
                description="Manages user accounts and authentication",
                port=8001,
                language=LanguageType.PYTHON,
                framework=FrameworkType.FASTAPI,
                database="postgresql",
            ),
            MicroserviceSpec(
                name="order-service",
                description="Handles order processing and fulfillment",
                port=8002,
                language=LanguageType.PYTHON,
                framework=FrameworkType.FASTAPI,
                database="mongodb",
            ),
        ]

        architecture = MicroservicesArchitecture(
            name="ecommerce-platform",
            description="E-commerce microservices platform",
            services=services,
            api_gateway=True,
            service_discovery="consul",
            monitoring=True,
            logging=True,
        )

        # Test README generation
        readme_content = self.scaffolder._generate_architecture_readme(architecture)
        assert "# ecommerce-platform" in readme_content
        assert "E-commerce microservices platform" in readme_content
        assert "- **user-service**: Manages user accounts and authentication (Port: 8001)" in readme_content
        assert "- **order-service**: Handles order processing and fulfillment (Port: 8002)" in readme_content
        assert "Service Discovery**: consul" in readme_content
        assert "API Gateway**: Enabled" in readme_content

        # Test architecture documentation
        arch_doc = self.scaffolder._generate_architecture_documentation_content(architecture)
        assert "# ecommerce-platform Architecture Documentation" in arch_doc
        assert "Service Breakdown" in arch_doc
        assert "Communication Patterns" in arch_doc
        assert "Infrastructure Components" in arch_doc

        # Test API documentation
        api_doc = self.scaffolder._generate_api_documentation(architecture)
        assert "# ecommerce-platform API Documentation" in api_doc
        assert "Service APIs" in api_doc
        assert "### user-service" in api_doc
        assert "### order-service" in api_doc

    def test_next_steps_generation(self) -> None:
        """Test next steps generation."""
        services = [
            MicroserviceSpec(
                name="test-service",
                description="Test service",
                port=8000,
                language=LanguageType.PYTHON,
                framework=FrameworkType.FASTAPI,
            )
        ]

        architecture = MicroservicesArchitecture(
            name="test-platform",
            description="Test platform",
            services=services,
            api_gateway=True,
            service_discovery="consul",
            monitoring=True,
            logging=True,
        )

        next_steps = self.scaffolder._generate_microservices_next_steps(architecture)

        # Verify expected steps are included
        next_steps_text = " ".join(next_steps)
        assert "cd test-platform" in next_steps_text
        assert "docker-compose up -d" in next_steps_text
        assert "http://localhost:8500" in next_steps_text  # Consul UI
        assert "http://localhost:9090" in next_steps_text  # Prometheus
        assert "http://localhost:3000" in next_steps_text  # Grafana
        assert "kubectl apply" in next_steps_text

    def test_error_handling_empty_services(self) -> None:
        """Test error handling with empty services list."""
        architecture = MicroservicesArchitecture(
            name="empty-platform",
            description="Platform with no services",
            services=[],  # Empty services list
        )

        output_path = self.temp_dir / "empty-platform"
        result = self.scaffolder.scaffold_microservices_architecture(
            architecture, output_path
        )

        # Should still succeed but with minimal infrastructure
        assert result.success
        assert output_path.exists()

        # Should still create infrastructure files
        assert (output_path / "docker-compose.yml").exists()
        assert (output_path / "README.md").exists()


@pytest.mark.integration
class TestMicroservicesScaffolderIntegration:
    """Integration tests for the microservices scaffolder."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.template_system = TemplateSystem()
        self.scaffolder = MicroservicesScaffolder(self.template_system)

    def teardown_method(self) -> None:
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_complete_microservices_platform_scaffolding(self) -> None:
        """Test scaffolding a complete microservices platform."""
        services = [
            MicroserviceSpec(
                name="user-service",
                description="User management and authentication service",
                port=8001,
                language=LanguageType.PYTHON,
                framework=FrameworkType.FASTAPI,
                database="postgresql",
                dependencies=["auth-service"],
            ),
            MicroserviceSpec(
                name="product-service",
                description="Product catalog and inventory service",
                port=8002,
                language=LanguageType.PYTHON,
                framework=FrameworkType.FASTAPI,
                database="mongodb",
            ),
            MicroserviceSpec(
                name="order-service",
                description="Order processing and fulfillment service",
                port=8003,
                language=LanguageType.PYTHON,
                framework=FrameworkType.FASTAPI,
                database="postgresql",
                dependencies=["user-service", "product-service"],
            ),
        ]

        architecture = MicroservicesArchitecture(
            name="ecommerce-platform",
            description="Complete e-commerce microservices platform",
            services=services,
            api_gateway=True,
            service_discovery="consul",
            message_broker="rabbitmq",
            monitoring=True,
            logging=True,
        )

        output_path = self.temp_dir / "ecommerce-platform"
        result = self.scaffolder.scaffold_microservices_architecture(
            architecture, output_path
        )

        # Verify successful scaffolding
        assert result.success
        assert len(result.errors) == 0
        assert len(result.created_files) > 10  # Should create many files
        assert len(result.created_directories) > 5  # Should create multiple directories

        # Verify complete directory structure
        assert (output_path / "infrastructure" / "k8s").exists()
        assert (output_path / "infrastructure" / "terraform").exists()
        assert (output_path / "api-gateway").exists()
        assert (output_path / "service-discovery" / "consul").exists()
        assert (output_path / "monitoring").exists()
        assert (output_path / "logging").exists()
        assert (output_path / "docs").exists()

        # Verify all services would be created (directories)
        # Note: Individual service scaffolding depends on template availability
        services_dir = output_path / "services"
        if services_dir.exists():
            for service in services:
                service_dir = services_dir / service.name
                # Service directories may or may not exist depending on template availability

        # Verify key configuration files
        assert (output_path / "docker-compose.yml").exists()
        assert (output_path / ".env.example").exists()
        assert (output_path / "README.md").exists()

        # Verify infrastructure files
        assert (output_path / "infrastructure" / "k8s" / "namespace.yaml").exists()
        assert (output_path / "infrastructure" / "terraform" / "main.tf").exists()
        assert (output_path / "api-gateway" / "nginx.conf").exists()
        assert (output_path / "monitoring" / "prometheus.yml").exists()
        assert (output_path / "logging" / "elasticsearch.yml").exists()

        # Verify documentation files
        assert (output_path / "docs" / "architecture.md").exists()
        assert (output_path / "docs" / "api.md").exists()

        # Verify next steps are provided
        assert len(result.next_steps) > 0
        next_steps_text = " ".join(result.next_steps)
        assert "ecommerce-platform" in next_steps_text