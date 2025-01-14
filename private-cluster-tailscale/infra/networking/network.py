# networking/network.py
from typing import Any, Dict
from pulumi import ComponentResource, ResourceOptions, export
from pulumi_gcp import compute
import yaml
import os

class Network(ComponentResource):
    """
    Network infrastructure component that creates and manages:
    - Shared VPC
    - Subnets for both clusters
    - Firewall rules
    """
    
    def __init__(self, config: Dict[str, Any], opts: ResourceOptions = None):
        super().__init__('hungry-echoes:network', config['network']['name'], None, opts)

        # Set the config object
        self.config = config

        # Create shared VPC
        self.vpc = compute.Network(
            resource_name=self.config['pulumi_provider']['network_provider_name'],
            name=self.config['network']['name'],
            auto_create_subnetworks=False,
            opts=ResourceOptions(parent=self)
        )

        # Create firewall rules for internal communication
        self._create_internal_firewall_rules()
        
        # Create firewall rules for health checks and metrics
        self._create_external_firewall_rules()

        # Create subnets for both clusters
        # Note: Regions are hardcoded for demo purposes. In production,
        # you might want to make these configurable in settings.yaml
        self.app_subnet = self._create_app_subnet()
        self.monitoring_subnet = self._create_monitoring_subnet()

        # Export network information for other components
        export('vpc_id', self.vpc.id)
        export('vpc_name', self.vpc.name)
        export('network_config', self.config['network'])
        export('app_subnet_id', self.app_subnet.id)
        export('monitoring_subnet_id', self.monitoring_subnet.id)

    def _create_internal_firewall_rules(self):
        """Create firewall rules for internal cluster communication."""
        
        # Collect all CIDR ranges
        internal_ranges = [
            self.config['network']['app_cluster']['subnet_cidr'],
            self.config['network']['app_cluster']['pods_cidr'],
            self.config['network']['app_cluster']['services_cidr'],
            self.config['network']['monitoring_cluster']['subnet_cidr'],
            self.config['network']['monitoring_cluster']['pods_cidr'],
            self.config['network']['monitoring_cluster']['services_cidr']
        ]


        self.allow_internal = compute.Firewall(
            self.config['pulumi_provider']['firewall_cluster_internal_allow_rule_provider_name'],
            network=self.vpc.name,
            allows=[
                {"protocol": "icmp"},
                {"protocol": "tcp", "ports": ["0-65535"]},
                {"protocol": "udp", "ports": ["0-65535"]}
            ],
            source_ranges=internal_ranges,
            opts=ResourceOptions(parent=self)
        )

    def _create_external_firewall_rules(self):
        """Create firewall rules for health checks and metrics."""
        
        # Create firewall rule for health checks
        self.allow_health_checks = compute.Firewall(
            self.config['pulumi_provider']['firewall_health_check_allow_rule_provider_name'],
            network=self.vpc.name,
            allows=[
                {
                    "protocol": "tcp",
                    "ports": ["80", "443", "8081"]  # Include metrics port
                }
            ],
            source_ranges=self.config['network']['health_check_ranges'],
            opts=ResourceOptions(parent=self)
        )

        # Create firewall rule for metrics
        self.allow_metrics = compute.Firewall(
            self.config['pulumi_provider']['firewall_metrics_allow_rule_provider_name'],
            network=self.vpc.name,
            allows=[
                {
                    "protocol": "tcp",
                    "ports": ["8081"]  # Metrics port
                }
            ],
            source_ranges=[
                self.config['network']['app_cluster']['subnet_cidr'],
                self.config['network']['app_cluster']['pods_cidr'], 
                self.config['network']['monitoring_cluster']['subnet_cidr'],
                self.config['network']['monitoring_cluster']['pods_cidr']
            ],
            opts=ResourceOptions(parent=self)
        )

    def _create_app_subnet(self):
        """Create subnet for app cluster in the specified region."""

        return compute.Subnetwork(
            self.config['pulumi_provider']['app_subnet_provider_name'],
            network=self.vpc.id,
            region=self.config['app_cluster']['region'],
            ip_cidr_range=self.config['network']['app_cluster']['subnet_cidr'],
            secondary_ip_ranges=[
                {
                    "range_name": "app-pods",
                    "ip_cidr_range": self.config['network']['app_cluster']['pods_cidr']
                },
                {
                    "range_name": "app-services",
                    "ip_cidr_range": self.config['network']['app_cluster']['services_cidr']
                }
            ],
            # Enable flow logs for monitoring
            log_config={
                "aggregation_interval": "INTERVAL_5_SEC",
                "flow_sampling": 0.5,
                "metadata": "INCLUDE_ALL_METADATA"
            },
            opts=ResourceOptions(parent=self)
        )

    def _create_monitoring_subnet(self):
        """Create subnet for monitoring cluster in the specified region."""
        return compute.Subnetwork(
            self.config['pulumi_provider']['monitoring_subnet_provider_name'],
            network=self.vpc.id,
            region=self.config['monitoring_cluster']['region'],
            ip_cidr_range=self.config['network']['monitoring_cluster']['subnet_cidr'],
            secondary_ip_ranges=[
                {
                    "range_name": "monitoring-pods",
                    "ip_cidr_range": self.config['network']['monitoring_cluster']['pods_cidr']
                },
                {
                    "range_name": "monitoring-services",
                    "ip_cidr_range": self.config['network']['monitoring_cluster']['services_cidr']
                }
            ],
            # Enable flow logs for monitoring
            log_config={
                "aggregation_interval": "INTERVAL_5_SEC",
                "flow_sampling": 0.5,
                "metadata": "INCLUDE_ALL_METADATA"
            },
            opts=ResourceOptions(parent=self)
        )