# monitoring_cluster/monitoring_cluster.py
from pulumi import ComponentResource, ResourceOptions, Output
from pulumi_gcp import container, compute
import yaml
import os

class MonitoringCluster(ComponentResource):
    """
    Monitoring cluster configuration that creates a GKE cluster
    for monitoring workloads. Uses networking configuration from
    the shared network component.
    """
    
    def __init__(self, 
                 name: str, 
                 vpc_id: Output,            # Add network parameters
                 subnet_id: Output,         # Add subnet parameters
                 opts: ResourceOptions = None):
        super().__init__('hungry-echoes:monitoring', name, None, opts)

        # Load cluster configuration
        config_path = os.path.join(os.path.dirname(__file__), '../settings.yaml')
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Create the monitoring GKE cluster
        self.cluster = container.Cluster(
            name,
            name=self.config['monitoring_cluster']['name'],
            location=self.config['monitoring_cluster']['zone'],
            
            # Remove default node pool
            initial_node_count=1,
            remove_default_node_pool=True,

            # Network configuration from passed parameters
            network=vpc_id,
            subnetwork=subnet_id,

            # IP allocation policy
            ip_allocation_policy={
                "cluster_secondary_range_name": "monitoring-pods",
                "services_secondary_range_name": "monitoring-services"
            },

            # Private cluster configuration
            private_cluster_config={
                "enable_private_nodes": False,
                "enable_private_endpoint": False,
                "master_ipv4_cidr_block": "172.16.1.0/28"  # Different from app cluster
            },

            # Use STABLE release channel for monitoring
            release_channel={
                "channel": "STABLE"
            },

            # Improve maintenance window configuration
            maintenance_policy={
                "daily_maintenance_window": {
                    "start_time": "10:00",  # UTC time (2:00 AM PST)
                }
            },

            # Enable workload identity
            workload_identity_config={
                "workload_pool": f"{self.config['project']['id']}.svc.id.goog"
            },

            # Disable deletion protection for development
            deletion_protection=False,

            opts=ResourceOptions(parent=self)
        )

        # Create node pool
        self.node_pool = container.NodePool(
            f"{name}-node-pool",
            name=f"{self.config['monitoring_cluster']['name']}-node-pool",
            location=self.config['monitoring_cluster']['zone'],
            cluster=self.cluster.name,
            node_count=self.config['node_pool']['node_count'],

            version=self.config['node_pool']['node_version'],

            node_config={
                "machine_type": self.config['node_pool']['monitoring_cluster']['machine_type'],
                "disk_size_gb": self.config['node_pool']['disk_size_gb'],
                "disk_type": self.config['node_pool']['disk_type'],
                "image_type": self.config['node_pool']['image_type'],

                # OAuth scopes
                "oauth_scopes": [
                    "https://www.googleapis.com/auth/logging.write",
                    "https://www.googleapis.com/auth/monitoring",
                    "https://www.googleapis.com/auth/devstorage.read_only"
                ],

                # Enable workload identity
                "workload_metadata_config": {
                    "mode": "GKE_METADATA"
                }
            },

            opts=ResourceOptions(parent=self)
        )

        # Register outputs
        self.register_outputs({
            "cluster_endpoint": self.cluster.endpoint,
            "cluster_name": self.cluster.name,
            "cluster_location": self.cluster.location
        })