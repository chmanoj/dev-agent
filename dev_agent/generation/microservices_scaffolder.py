"""Microservices scaffolding system with service discovery and communication patterns."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from ..models.enums import CICDPlatform, FrameworkType, LanguageType
from ..models.templates import (
    DirectoryTemplate,
    FileTemplate,
    ProjectSpec,
    ProjectTemplate,
    ScaffoldingResult,
)
from .template_system import TemplateSystem


class MicroserviceSpec:
    """Specification for a single microservice."""

    def __init__(
        self,
        name: str,
        description: str,
        port: int,
        language: LanguageType,
        framework: FrameworkType,
        database: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
    ):
        self.name = name
        self.description = description
        self.port = port
        self.language = language
        self.framework = framework
        self.database = database
        self.dependencies = dependencies or []


class MicroservicesArchitecture:
    """Definition of a complete microservices architecture."""

    def __init__(
        self,
        name: str,
        description: str,
        services: List[MicroserviceSpec],
        api_gateway: bool = True,
        service_discovery: str = "consul",
        message_broker: Optional[str] = "rabbitmq",
        monitoring: bool = True,
        logging: bool = True,
    ):
        self.name = name
        self.description = description
        self.services = services
        self.api_gateway = api_gateway
        self.service_discovery = service_discovery
        self.message_broker = message_broker
        self.monitoring = monitoring
        self.logging = logging


class MicroservicesScaffolder:
    """Scaffolder for microservices architectures."""

    def __init__(self, template_system: TemplateSystem):
        self.template_system = template_system

    def scaffold_microservices_architecture(
        self,
        architecture: MicroservicesArchitecture,
        output_path: Path,
    ) -> ScaffoldingResult:
        """Scaffold a complete microservices architecture.
        
        Args:
            architecture: Microservices architecture specification
            output_path: Directory where architecture should be created
            
        Returns:
            ScaffoldingResult with details of the scaffolding operation
        """
        result = ScaffoldingResult(
            success=True,
            project_path=output_path,
            created_files=[],
            created_directories=[],
            errors=[],
            warnings=[],
            next_steps=[]
        )

        try:
            # Create root directory
            output_path.mkdir(parents=True, exist_ok=True)
            result.created_directories.append(output_path)

            # Create infrastructure components
            self._create_infrastructure_configs(architecture, output_path, result)
            
            # Create individual services
            for service in architecture.services:
                service_path = output_path / "services" / service.name
                service_result = self._scaffold_individual_service(service, service_path)
                
                # Merge results
                result.created_files.extend(service_result.created_files)
                result.created_directories.extend(service_result.created_directories)
                result.errors.extend(service_result.errors)
                result.warnings.extend(service_result.warnings)

            # Create API Gateway if requested
            if architecture.api_gateway:
                self._create_api_gateway(architecture, output_path, result)

            # Create service discovery configuration
            self._create_service_discovery_config(architecture, output_path, result)

            # Create monitoring and logging setup
            if architecture.monitoring:
                self._create_monitoring_setup(architecture, output_path, result)
            
            if architecture.logging:
                self._create_logging_setup(architecture, output_path, result)

            # Create docker-compose for local development
            self._create_docker_compose(architecture, output_path, result)

            # Create root documentation
            self._create_architecture_documentation(architecture, output_path, result)

            # Generate next steps
            result.next_steps = self._generate_microservices_next_steps(architecture)

        except Exception as e:
            result.success = False
            result.errors.append(f"Microservices scaffolding failed: {str(e)}")

        return result

    def _scaffold_individual_service(
        self,
        service: MicroserviceSpec,
        service_path: Path,
    ) -> ScaffoldingResult:
        """Scaffold an individual microservice."""
        # Create project spec for the service
        project_spec = ProjectSpec(
            name=service.name,
            description=service.description,
            project_type="api_service",  # Assuming this maps to ProjectType.API_SERVICE
            primary_language=service.language,
            frameworks=[service.framework],
            include_docker=True,
            include_testing=True,
            include_linting=True,
            include_docs=True,
        )

        # Use the template system to scaffold the service
        return self.template_system.create_project_scaffold(project_spec, service_path)

    def _create_infrastructure_configs(
        self,
        architecture: MicroservicesArchitecture,
        output_path: Path,
        result: ScaffoldingResult,
    ) -> None:
        """Create infrastructure configuration files."""
        infra_path = output_path / "infrastructure"
        infra_path.mkdir(parents=True, exist_ok=True)
        result.created_directories.append(infra_path)

        # Create Kubernetes manifests
        k8s_path = infra_path / "k8s"
        k8s_path.mkdir(parents=True, exist_ok=True)
        result.created_directories.append(k8s_path)

        # Create namespace
        namespace_content = self._generate_k8s_namespace(architecture)
        namespace_file = k8s_path / "namespace.yaml"
        namespace_file.write_text(namespace_content)
        result.created_files.append(namespace_file)

        # Create service manifests for each microservice
        for service in architecture.services:
            service_manifest = self._generate_k8s_service_manifest(service)
            service_file = k8s_path / f"{service.name}-service.yaml"
            service_file.write_text(service_manifest)
            result.created_files.append(service_file)

            deployment_manifest = self._generate_k8s_deployment_manifest(service)
            deployment_file = k8s_path / f"{service.name}-deployment.yaml"
            deployment_file.write_text(deployment_manifest)
            result.created_files.append(deployment_file)

        # Create Terraform configuration
        terraform_path = infra_path / "terraform"
        terraform_path.mkdir(parents=True, exist_ok=True)
        result.created_directories.append(terraform_path)

        terraform_main = self._generate_terraform_main(architecture)
        terraform_file = terraform_path / "main.tf"
        terraform_file.write_text(terraform_main)
        result.created_files.append(terraform_file)

    def _create_api_gateway(
        self,
        architecture: MicroservicesArchitecture,
        output_path: Path,
        result: ScaffoldingResult,
    ) -> None:
        """Create API Gateway configuration."""
        gateway_path = output_path / "api-gateway"
        gateway_path.mkdir(parents=True, exist_ok=True)
        result.created_directories.append(gateway_path)

        # Create nginx configuration for API Gateway
        nginx_config = self._generate_nginx_gateway_config(architecture)
        nginx_file = gateway_path / "nginx.conf"
        nginx_file.write_text(nginx_config)
        result.created_files.append(nginx_file)

        # Create Dockerfile for API Gateway
        dockerfile_content = self._generate_gateway_dockerfile()
        dockerfile = gateway_path / "Dockerfile"
        dockerfile.write_text(dockerfile_content)
        result.created_files.append(dockerfile)

    def _create_service_discovery_config(
        self,
        architecture: MicroservicesArchitecture,
        output_path: Path,
        result: ScaffoldingResult,
    ) -> None:
        """Create service discovery configuration."""
        if architecture.service_discovery == "consul":
            consul_path = output_path / "service-discovery" / "consul"
            consul_path.mkdir(parents=True, exist_ok=True)
            result.created_directories.append(consul_path)

            consul_config = self._generate_consul_config(architecture)
            consul_file = consul_path / "consul.json"
            consul_file.write_text(consul_config)
            result.created_files.append(consul_file)

    def _create_monitoring_setup(
        self,
        architecture: MicroservicesArchitecture,
        output_path: Path,
        result: ScaffoldingResult,
    ) -> None:
        """Create monitoring setup with Prometheus and Grafana."""
        monitoring_path = output_path / "monitoring"
        monitoring_path.mkdir(parents=True, exist_ok=True)
        result.created_directories.append(monitoring_path)

        # Prometheus configuration
        prometheus_config = self._generate_prometheus_config(architecture)
        prometheus_file = monitoring_path / "prometheus.yml"
        prometheus_file.write_text(prometheus_config)
        result.created_files.append(prometheus_file)

        # Grafana dashboard
        grafana_dashboard = self._generate_grafana_dashboard(architecture)
        grafana_file = monitoring_path / "grafana-dashboard.json"
        grafana_file.write_text(grafana_dashboard)
        result.created_files.append(grafana_file)

    def _create_logging_setup(
        self,
        architecture: MicroservicesArchitecture,
        output_path: Path,
        result: ScaffoldingResult,
    ) -> None:
        """Create centralized logging setup with ELK stack."""
        logging_path = output_path / "logging"
        logging_path.mkdir(parents=True, exist_ok=True)
        result.created_directories.append(logging_path)

        # Elasticsearch configuration
        elasticsearch_config = self._generate_elasticsearch_config()
        elasticsearch_file = logging_path / "elasticsearch.yml"
        elasticsearch_file.write_text(elasticsearch_config)
        result.created_files.append(elasticsearch_file)

        # Logstash configuration
        logstash_config = self._generate_logstash_config(architecture)
        logstash_file = logging_path / "logstash.conf"
        logstash_file.write_text(logstash_config)
        result.created_files.append(logstash_file)

        # Kibana configuration
        kibana_config = self._generate_kibana_config()
        kibana_file = logging_path / "kibana.yml"
        kibana_file.write_text(kibana_config)
        result.created_files.append(kibana_file)

    def _create_docker_compose(
        self,
        architecture: MicroservicesArchitecture,
        output_path: Path,
        result: ScaffoldingResult,
    ) -> None:
        """Create docker-compose for local development."""
        docker_compose_content = self._generate_docker_compose_content(architecture)
        docker_compose_file = output_path / "docker-compose.yml"
        docker_compose_file.write_text(docker_compose_content)
        result.created_files.append(docker_compose_file)

        # Create development environment file
        env_content = self._generate_env_file(architecture)
        env_file = output_path / ".env.example"
        env_file.write_text(env_content)
        result.created_files.append(env_file)

    def _create_architecture_documentation(
        self,
        architecture: MicroservicesArchitecture,
        output_path: Path,
        result: ScaffoldingResult,
    ) -> None:
        """Create architecture documentation."""
        docs_path = output_path / "docs"
        docs_path.mkdir(parents=True, exist_ok=True)
        result.created_directories.append(docs_path)

        # Main README
        readme_content = self._generate_architecture_readme(architecture)
        readme_file = output_path / "README.md"
        readme_file.write_text(readme_content)
        result.created_files.append(readme_file)

        # Architecture documentation
        arch_doc_content = self._generate_architecture_documentation_content(architecture)
        arch_doc_file = docs_path / "architecture.md"
        arch_doc_file.write_text(arch_doc_content)
        result.created_files.append(arch_doc_file)

        # API documentation
        api_doc_content = self._generate_api_documentation(architecture)
        api_doc_file = docs_path / "api.md"
        api_doc_file.write_text(api_doc_content)
        result.created_files.append(api_doc_file)

    # Template generation methods
    def _generate_k8s_namespace(self, architecture: MicroservicesArchitecture) -> str:
        """Generate Kubernetes namespace manifest."""
        return f"""apiVersion: v1
kind: Namespace
metadata:
  name: {architecture.name}
  labels:
    name: {architecture.name}
"""

    def _generate_k8s_service_manifest(self, service: MicroserviceSpec) -> str:
        """Generate Kubernetes service manifest."""
        return f"""apiVersion: v1
kind: Service
metadata:
  name: {service.name}
  labels:
    app: {service.name}
spec:
  selector:
    app: {service.name}
  ports:
    - protocol: TCP
      port: {service.port}
      targetPort: {service.port}
  type: ClusterIP
"""

    def _generate_k8s_deployment_manifest(self, service: MicroserviceSpec) -> str:
        """Generate Kubernetes deployment manifest."""
        return f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {service.name}
  labels:
    app: {service.name}
spec:
  replicas: 3
  selector:
    matchLabels:
      app: {service.name}
  template:
    metadata:
      labels:
        app: {service.name}
    spec:
      containers:
      - name: {service.name}
        image: {service.name}:latest
        ports:
        - containerPort: {service.port}
        env:
        - name: PORT
          value: "{service.port}"
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
"""

    def _generate_terraform_main(self, architecture: MicroservicesArchitecture) -> str:
        """Generate Terraform main configuration."""
        return f"""terraform {{
  required_version = ">= 1.0"
  required_providers {{
    kubernetes = {{
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }}
  }}
}}

provider "kubernetes" {{
  config_path = "~/.kube/config"
}}

resource "kubernetes_namespace" "{architecture.name}" {{
  metadata {{
    name = "{architecture.name}"
  }}
}}

# Service resources
{self._generate_terraform_services(architecture.services)}
"""

    def _generate_terraform_services(self, services: List[MicroserviceSpec]) -> str:
        """Generate Terraform service resources."""
        terraform_services = []
        for service in services:
            terraform_services.append(f"""
resource "kubernetes_deployment" "{service.name}" {{
  metadata {{
    name      = "{service.name}"
    namespace = kubernetes_namespace.{service.name.replace('-', '_')}.metadata[0].name
  }}
  spec {{
    replicas = 3
    selector {{
      match_labels = {{
        app = "{service.name}"
      }}
    }}
    template {{
      metadata {{
        labels = {{
          app = "{service.name}"
        }}
      }}
      spec {{
        container {{
          name  = "{service.name}"
          image = "{service.name}:latest"
          port {{
            container_port = {service.port}
          }}
        }}
      }}
    }}
  }}
}}

resource "kubernetes_service" "{service.name}" {{
  metadata {{
    name      = "{service.name}"
    namespace = kubernetes_namespace.{service.name.replace('-', '_')}.metadata[0].name
  }}
  spec {{
    selector = {{
      app = "{service.name}"
    }}
    port {{
      port        = {service.port}
      target_port = {service.port}
    }}
  }}
}}""")
        return "\n".join(terraform_services)

    def _generate_nginx_gateway_config(self, architecture: MicroservicesArchitecture) -> str:
        """Generate nginx configuration for API Gateway."""
        upstream_configs = []
        location_configs = []
        
        for service in architecture.services:
            upstream_configs.append(f"""
upstream {service.name} {{
    server {service.name}:{service.port};
}}""")
            
            location_configs.append(f"""
    location /{service.name}/ {{
        proxy_pass http://{service.name}/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}""")

        return f"""events {{
    worker_connections 1024;
}}

http {{
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;
    
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;
    error_log /var/log/nginx/error.log;

    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Upstream configurations
    {''.join(upstream_configs)}

    server {{
        listen 80;
        server_name localhost;

        # Health check endpoint
        location /health {{
            access_log off;
            return 200 "healthy\\n";
            add_header Content-Type text/plain;
        }}

        # Service routes
        {''.join(location_configs)}
    }}
}}"""

    def _generate_gateway_dockerfile(self) -> str:
        """Generate Dockerfile for API Gateway."""
        return """FROM nginx:alpine

COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
"""

    def _generate_consul_config(self, architecture: MicroservicesArchitecture) -> str:
        """Generate Consul configuration."""
        import json
        
        config = {
            "datacenter": "dc1",
            "data_dir": "/opt/consul/data",
            "log_level": "INFO",
            "server": True,
            "bootstrap_expect": 1,
            "bind_addr": "0.0.0.0",
            "client_addr": "0.0.0.0",
            "ui_config": {
                "enabled": True
            },
            "services": [
                {
                    "name": service.name,
                    "port": service.port,
                    "check": {
                        "http": f"http://localhost:{service.port}/health",
                        "interval": "10s"
                    }
                }
                for service in architecture.services
            ]
        }
        
        return json.dumps(config, indent=2)

    def _generate_prometheus_config(self, architecture: MicroservicesArchitecture) -> str:
        """Generate Prometheus configuration."""
        scrape_configs = []
        for service in architecture.services:
            scrape_configs.append(f"""
  - job_name: '{service.name}'
    static_configs:
      - targets: ['{service.name}:{service.port}']
    metrics_path: /metrics
    scrape_interval: 15s""")

        return f"""global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
{''.join(scrape_configs)}
"""

    def _generate_grafana_dashboard(self, architecture: MicroservicesArchitecture) -> str:
        """Generate Grafana dashboard configuration."""
        import json
        
        dashboard = {
            "dashboard": {
                "id": None,
                "title": f"{architecture.name} Microservices Dashboard",
                "tags": ["microservices"],
                "timezone": "browser",
                "panels": [
                    {
                        "id": i + 1,
                        "title": f"{service.name} Metrics",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": f"up{{job=\"{service.name}\"}}",
                                "legendFormat": f"{service.name} Status"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": i * 8}
                    }
                    for i, service in enumerate(architecture.services)
                ],
                "time": {"from": "now-1h", "to": "now"},
                "timepicker": {},
                "templating": {"list": []},
                "annotations": {"list": []},
                "refresh": "5s",
                "schemaVersion": 16,
                "version": 0
            }
        }
        
        return json.dumps(dashboard, indent=2)

    def _generate_elasticsearch_config(self) -> str:
        """Generate Elasticsearch configuration."""
        return """cluster.name: "microservices-logs"
node.name: "elasticsearch-node-1"
network.host: 0.0.0.0
http.port: 9200
discovery.type: single-node
xpack.security.enabled: false
"""

    def _generate_logstash_config(self, architecture: MicroservicesArchitecture) -> str:
        """Generate Logstash configuration."""
        return """input {
  beats {
    port => 5044
  }
}

filter {
  if [fields][service] {
    mutate {
      add_field => { "service_name" => "%{[fields][service]}" }
    }
  }
  
  # Parse JSON logs
  if [message] =~ /^{.*}$/ {
    json {
      source => "message"
    }
  }
  
  # Add timestamp
  date {
    match => [ "timestamp", "ISO8601" ]
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "microservices-logs-%{+YYYY.MM.dd}"
  }
  
  stdout {
    codec => rubydebug
  }
}
"""

    def _generate_kibana_config(self) -> str:
        """Generate Kibana configuration."""
        return """server.name: kibana
server.host: "0.0.0.0"
elasticsearch.hosts: ["http://elasticsearch:9200"]
monitoring.ui.container.elasticsearch.enabled: true
"""

    def _generate_docker_compose_content(self, architecture: MicroservicesArchitecture) -> str:
        """Generate docker-compose.yml content."""
        services = []
        
        # Add microservices
        for service in architecture.services:
            services.append(f"""
  {service.name}:
    build: ./services/{service.name}
    ports:
      - "{service.port}:{service.port}"
    environment:
      - PORT={service.port}
      - SERVICE_NAME={service.name}
    depends_on:
      - consul
    networks:
      - microservices""")

        # Add infrastructure services
        if architecture.service_discovery == "consul":
            services.append("""
  consul:
    image: consul:latest
    ports:
      - "8500:8500"
    volumes:
      - ./service-discovery/consul/consul.json:/consul/config/consul.json
    networks:
      - microservices""")

        if architecture.api_gateway:
            services.append("""
  api-gateway:
    build: ./api-gateway
    ports:
      - "80:80"
    depends_on:
      - consul
    networks:
      - microservices""")

        if architecture.monitoring:
            services.extend(["""
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    networks:
      - microservices""", """
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - ./monitoring/grafana-dashboard.json:/var/lib/grafana/dashboards/dashboard.json
    networks:
      - microservices"""])

        if architecture.logging:
            services.extend(["""
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.14.0
    ports:
      - "9200:9200"
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - ./logging/elasticsearch.yml:/usr/share/elasticsearch/config/elasticsearch.yml
    networks:
      - microservices""", """
  logstash:
    image: docker.elastic.co/logstash/logstash:7.14.0
    ports:
      - "5044:5044"
    volumes:
      - ./logging/logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    depends_on:
      - elasticsearch
    networks:
      - microservices""", """
  kibana:
    image: docker.elastic.co/kibana/kibana:7.14.0
    ports:
      - "5601:5601"
    volumes:
      - ./logging/kibana.yml:/usr/share/kibana/config/kibana.yml
    depends_on:
      - elasticsearch
    networks:
      - microservices"""])

        return f"""version: '3.8'

services:{''.join(services)}

networks:
  microservices:
    driver: bridge

volumes:
  consul_data:
  prometheus_data:
  grafana_data:
  elasticsearch_data:
"""

    def _generate_env_file(self, architecture: MicroservicesArchitecture) -> str:
        """Generate environment file template."""
        env_vars = [
            "# Microservices Environment Configuration",
            f"COMPOSE_PROJECT_NAME={architecture.name}",
            "",
            "# Service Discovery",
            "CONSUL_HOST=consul",
            "CONSUL_PORT=8500",
            "",
            "# Monitoring",
            "PROMETHEUS_HOST=prometheus",
            "PROMETHEUS_PORT=9090",
            "GRAFANA_HOST=grafana",
            "GRAFANA_PORT=3000",
            "GRAFANA_ADMIN_PASSWORD=admin",
            "",
            "# Logging",
            "ELASTICSEARCH_HOST=elasticsearch",
            "ELASTICSEARCH_PORT=9200",
            "KIBANA_HOST=kibana",
            "KIBANA_PORT=5601",
            "",
        ]
        
        # Add service-specific environment variables
        for service in architecture.services:
            env_vars.extend([
                f"# {service.name.upper()} Service",
                f"{service.name.upper()}_PORT={service.port}",
                f"{service.name.upper()}_HOST={service.name}",
                "",
            ])
        
        return "\n".join(env_vars)

    def _generate_architecture_readme(self, architecture: MicroservicesArchitecture) -> str:
        """Generate main README for the architecture."""
        services_list = "\n".join([f"- **{s.name}**: {s.description} (Port: {s.port})" for s in architecture.services])
        
        return f"""# {architecture.name}

{architecture.description}

## Architecture Overview

This microservices architecture consists of the following services:

{services_list}

## Infrastructure Components

- **Service Discovery**: {architecture.service_discovery}
- **API Gateway**: {'Enabled' if architecture.api_gateway else 'Disabled'}
- **Message Broker**: {architecture.message_broker or 'None'}
- **Monitoring**: {'Enabled (Prometheus + Grafana)' if architecture.monitoring else 'Disabled'}
- **Logging**: {'Enabled (ELK Stack)' if architecture.logging else 'Disabled'}

## Quick Start

1. **Prerequisites**
   - Docker and Docker Compose
   - kubectl (for Kubernetes deployment)
   - Terraform (for infrastructure provisioning)

2. **Local Development**
   ```bash
   # Copy environment file
   cp .env.example .env
   
   # Start all services
   docker-compose up -d
   
   # Check service status
   docker-compose ps
   ```

3. **Access Services**
   - API Gateway: http://localhost
   - Consul UI: http://localhost:8500
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3000 (admin/admin)
   - Kibana: http://localhost:5601

## Development

### Building Individual Services

Each service can be built and run independently:

```bash
cd services/[service-name]
docker build -t [service-name] .
docker run -p [port]:[port] [service-name]
```

### Testing

Run tests for all services:

```bash
# Run unit tests for each service
for service in services/*/; do
    echo "Testing $service"
    cd "$service"
    # Add service-specific test commands here
    cd ../..
done
```

## Deployment

### Kubernetes

1. **Deploy to Kubernetes**
   ```bash
   kubectl apply -f infrastructure/k8s/
   ```

2. **Check deployment status**
   ```bash
   kubectl get pods -n {architecture.name}
   kubectl get services -n {architecture.name}
   ```

### Terraform

1. **Initialize Terraform**
   ```bash
   cd infrastructure/terraform
   terraform init
   ```

2. **Plan and apply**
   ```bash
   terraform plan
   terraform apply
   ```

## Monitoring and Observability

- **Metrics**: Prometheus collects metrics from all services
- **Dashboards**: Grafana provides visualization dashboards
- **Logs**: Centralized logging with ELK stack
- **Tracing**: (Add distributed tracing setup as needed)

## API Documentation

See [docs/api.md](docs/api.md) for detailed API documentation.

## Architecture Documentation

See [docs/architecture.md](docs/architecture.md) for detailed architecture documentation.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

[Add your license here]
"""

    def _generate_architecture_documentation_content(self, architecture: MicroservicesArchitecture) -> str:
        """Generate detailed architecture documentation."""
        return f"""# {architecture.name} Architecture Documentation

## Overview

{architecture.description}

## Service Architecture

### Service Breakdown

{self._generate_service_breakdown_docs(architecture.services)}

## Communication Patterns

### Synchronous Communication
- HTTP/REST APIs for request-response patterns
- API Gateway routes external requests to appropriate services

### Asynchronous Communication
{f"- Message broker: {architecture.message_broker}" if architecture.message_broker else "- No message broker configured"}
- Event-driven architecture for loose coupling

## Data Management

### Database per Service Pattern
Each service manages its own data store to ensure loose coupling and independent deployability.

{self._generate_database_docs(architecture.services)}

## Infrastructure Components

### Service Discovery
- **Technology**: {architecture.service_discovery}
- **Purpose**: Automatic service registration and discovery
- **Health Checks**: Automated health monitoring

### API Gateway
{f"- **Enabled**: Routes external traffic to internal services" if architecture.api_gateway else "- **Disabled**: Direct service access"}
- **Load Balancing**: Distributes requests across service instances
- **Rate Limiting**: Protects services from overload

### Monitoring Stack
{f"- **Prometheus**: Metrics collection and alerting" if architecture.monitoring else "- **Monitoring**: Disabled"}
{f"- **Grafana**: Metrics visualization and dashboards" if architecture.monitoring else ""}

### Logging Stack
{f"- **Elasticsearch**: Log storage and indexing" if architecture.logging else "- **Logging**: Disabled"}
{f"- **Logstash**: Log processing and transformation" if architecture.logging else ""}
{f"- **Kibana**: Log visualization and analysis" if architecture.logging else ""}

## Deployment Strategy

### Containerization
- Each service is containerized using Docker
- Multi-stage builds for optimized image sizes
- Health checks included in container definitions

### Orchestration
- Kubernetes for production deployments
- Docker Compose for local development
- Helm charts for package management (future enhancement)

### CI/CD Pipeline
- Automated testing for each service
- Container image building and scanning
- Automated deployment to staging and production

## Security Considerations

### Network Security
- Service-to-service communication within private networks
- API Gateway as the single entry point
- Network policies to restrict inter-service communication

### Authentication and Authorization
- JWT tokens for stateless authentication
- Service-to-service authentication using mutual TLS
- Role-based access control (RBAC)

### Data Security
- Encryption at rest for sensitive data
- Encryption in transit using TLS
- Secrets management using Kubernetes secrets or external vault

## Scalability and Performance

### Horizontal Scaling
- Stateless service design enables horizontal scaling
- Load balancing across multiple service instances
- Auto-scaling based on CPU/memory metrics

### Performance Optimization
- Connection pooling for database connections
- Caching strategies (Redis/Memcached)
- CDN for static content delivery

## Resilience Patterns

### Circuit Breaker
- Prevents cascade failures
- Automatic fallback mechanisms
- Configurable failure thresholds

### Retry Logic
- Exponential backoff for transient failures
- Maximum retry limits
- Dead letter queues for failed messages

### Bulkhead Pattern
- Resource isolation between services
- Separate thread pools for different operations
- Resource quotas and limits

## Observability

### Metrics
- Business metrics (transactions, user actions)
- Technical metrics (response times, error rates)
- Infrastructure metrics (CPU, memory, disk)

### Logging
- Structured logging with correlation IDs
- Centralized log aggregation
- Log retention policies

### Tracing
- Distributed tracing for request flows
- Performance bottleneck identification
- Service dependency mapping

## Development Guidelines

### Service Design Principles
- Single Responsibility Principle
- Database per Service
- Decentralized Governance
- Failure Isolation

### API Design
- RESTful API design
- Versioning strategy
- Backward compatibility
- OpenAPI/Swagger documentation

### Testing Strategy
- Unit tests for individual components
- Integration tests for service interactions
- Contract testing for API compatibility
- End-to-end tests for critical user journeys

## Operational Procedures

### Deployment
- Blue-green deployments for zero downtime
- Canary releases for gradual rollouts
- Rollback procedures for failed deployments

### Monitoring and Alerting
- SLA/SLO definitions
- Alert thresholds and escalation procedures
- On-call rotation and incident response

### Backup and Recovery
- Database backup strategies
- Disaster recovery procedures
- Business continuity planning
"""

    def _generate_service_breakdown_docs(self, services: List[MicroserviceSpec]) -> str:
        """Generate documentation for service breakdown."""
        docs = []
        for service in services:
            docs.append(f"""
#### {service.name}
- **Description**: {service.description}
- **Language**: {service.language.value}
- **Framework**: {service.framework.value}
- **Port**: {service.port}
- **Database**: {service.database or 'None'}
- **Dependencies**: {', '.join(service.dependencies) if service.dependencies else 'None'}
""")
        return "\n".join(docs)

    def _generate_database_docs(self, services: List[MicroserviceSpec]) -> str:
        """Generate database documentation for services."""
        docs = []
        for service in services:
            if service.database:
                docs.append(f"- **{service.name}**: {service.database}")
        
        if docs:
            return "\n" + "\n".join(docs)
        else:
            return "\n- No databases configured"

    def _generate_api_documentation(self, architecture: MicroservicesArchitecture) -> str:
        """Generate API documentation."""
        return f"""# {architecture.name} API Documentation

## Overview

This document describes the APIs provided by the {architecture.name} microservices architecture.

## API Gateway

{f"The API Gateway serves as the single entry point for all external requests. All service APIs are accessible through the gateway at their respective paths." if architecture.api_gateway else "No API Gateway is configured. Services are accessed directly."}

## Service APIs

{self._generate_service_api_docs(architecture.services)}

## Authentication

### JWT Token Authentication
All API endpoints require authentication using JWT tokens.

```http
Authorization: Bearer <jwt-token>
```

### Service-to-Service Authentication
Internal service communication uses mutual TLS authentication.

## Error Handling

### Standard Error Response Format
```json
{{
  "error": {{
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": {{
      "field": "Additional error details"
    }}
  }},
  "timestamp": "2023-01-01T00:00:00Z",
  "path": "/api/endpoint",
  "requestId": "unique-request-id"
}}
```

### HTTP Status Codes
- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

## Rate Limiting

API requests are rate limited to prevent abuse:
- **Authenticated users**: 1000 requests per hour
- **Unauthenticated requests**: 100 requests per hour

Rate limit headers are included in responses:
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## Versioning

APIs use URL path versioning:
```
/api/v1/endpoint
/api/v2/endpoint
```

## OpenAPI Specifications

Each service provides OpenAPI (Swagger) specifications:
{self._generate_openapi_links(architecture.services)}

## Testing

### Postman Collection
Import the Postman collection for easy API testing:
```bash
# Collection available at: ./docs/postman-collection.json
```

### cURL Examples
{self._generate_curl_examples(architecture.services)}
"""

    def _generate_service_api_docs(self, services: List[MicroserviceSpec]) -> str:
        """Generate API documentation for each service."""
        docs = []
        for service in services:
            docs.append(f"""
### {service.name}

**Base URL**: `http://localhost:{service.port}` (direct) or `/api/{service.name}` (via gateway)

**Description**: {service.description}

#### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check endpoint |
| GET | `/metrics` | Prometheus metrics |
| GET | `/api/v1/...` | Service-specific endpoints |

#### Health Check
```http
GET /health
```

Response:
```json
{{
  "status": "healthy",
  "timestamp": "2023-01-01T00:00:00Z",
  "version": "1.0.0"
}}
```
""")
        return "\n".join(docs)

    def _generate_openapi_links(self, services: List[MicroserviceSpec]) -> str:
        """Generate OpenAPI specification links."""
        links = []
        for service in services:
            links.append(f"- **{service.name}**: http://localhost:{service.port}/docs")
        return "\n" + "\n".join(links)

    def _generate_curl_examples(self, services: List[MicroserviceSpec]) -> str:
        """Generate cURL examples for services."""
        examples = []
        for service in services:
            examples.append(f"""
#### {service.name} Examples

```bash
# Health check
curl -X GET http://localhost:{service.port}/health

# Get service info (example)
curl -X GET http://localhost:{service.port}/api/v1/info \\
  -H "Authorization: Bearer <jwt-token>"
```""")
        return "\n".join(examples)

    def _generate_microservices_next_steps(self, architecture: MicroservicesArchitecture) -> List[str]:
        """Generate next steps for microservices setup."""
        steps = [
            f"cd {architecture.name}",
            "cp .env.example .env  # Configure environment variables",
            "docker-compose up -d  # Start all services",
            "docker-compose ps  # Check service status",
        ]

        if architecture.service_discovery == "consul":
            steps.append("# Access Consul UI: http://localhost:8500")

        if architecture.api_gateway:
            steps.append("# Access API Gateway: http://localhost")

        if architecture.monitoring:
            steps.extend([
                "# Access Prometheus: http://localhost:9090",
                "# Access Grafana: http://localhost:3000 (admin/admin)",
            ])

        if architecture.logging:
            steps.append("# Access Kibana: http://localhost:5601")

        steps.extend([
            "# Deploy to Kubernetes: kubectl apply -f infrastructure/k8s/",
            "# Provision infrastructure: cd infrastructure/terraform && terraform apply",
        ])

        return steps