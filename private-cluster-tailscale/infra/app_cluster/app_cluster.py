# app_cluster/app_cluster.py
import pulumi
from pulumi import ComponentResource, ResourceOptions, Output
from pulumi_gcp import container, projects
import yaml
import os

class AppCluster(ComponentResource):
    """
    App cluster configuration that creates a GKE cluster
    for the main application workload with improved error handling
    and update strategies.
    """
    
    def __init__(self, 
                 name: str, 
                 vpc_id: Output,           
                 subnet_id: Output,         
                 opts: ResourceOptions = None):
        super().__init__('hungry-echoes:app', name, None, opts)

        # Load app cluster configuration
        config_path = os.path.join(os.path.dirname(__file__), '../settings.yaml')
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        # Enable required GCP APIs with improved error handling
        self.services = self._enable_gcp_services(name)

        # Create the GKE cluster with improved configuration
        self.cluster = self._create_gke_cluster(name, vpc_id, subnet_id)

        # Create node pool with complete configuration
        self.node_pool = self._create_node_pool(name)

        # Register outputs
        self.register_outputs({
            "cluster_name": self.cluster.name,
            "cluster_endpoint": self.cluster.endpoint,
            "cluster_location": self.cluster.location
        })

    def _enable_gcp_services(self, name: str):
        """
        Enables required GCP APIs with proper error handling and retries.
        """
        required_services = [
            "container.googleapis.com",     
            "compute.googleapis.com",       
            "monitoring.googleapis.com",    
            "logging.googleapis.com",       
        ]

        services = []
        for service in required_services:
            enabled_service = projects.Service(
                f"{name}-{service}",
                project=self.config['project']['id'],
                service=service,
                disable_dependent_services=False,
                disable_on_destroy=False,
                opts=ResourceOptions(
                    parent=self,
                    # Add custom timeouts for API enablement
                    custom_timeouts=pulumi.CustomTimeouts(
                        create="10m",
                        delete="10m"
                    )
                )
            )
            services.append(enabled_service)
        
        return services

    def _create_gke_cluster(self, name: str, vpc_id: Output, subnet_id: Output):
        """
        Creates GKE cluster with improved configuration and error handling.
        """
        return container.Cluster(
            name,
            name=self.config['app_cluster']['name'],
            location=self.config['app_cluster']['zone'],

            # Remove default node pool
            initial_node_count=1,
            remove_default_node_pool=True,

            # Use the STABLE release channel for managed upgrades
            release_channel={   
                "channel": "STABLE"
            },

            # Improve maintenance window configuration
            maintenance_policy={
                "daily_maintenance_window": {
                    "start_time": "10:00",  # UTC time (2:00 AM PST)
                }
            },

            # Network configuration
            network=vpc_id,
            subnetwork=subnet_id,

            # IP allocation policy
            ip_allocation_policy={
                "cluster_secondary_range_name": "app-pods",
                "services_secondary_range_name": "app-services"
            },

            # Enable workload identity
            workload_identity_config={
                "workload_pool": f"{self.config['project']['id']}.svc.id.goog"
            },

            # Disable deletion protection for development
            deletion_protection=False,

            opts=ResourceOptions(
                parent=self,
                depends_on=self.services
            )
        )

    def _create_node_pool(self, name: str):
        """
        Creates node pool with complete configuration addressing the 
        missing attributes error.
        """
        return container.NodePool(
            f"{name}-node-pool",
            name=f"{self.config['app_cluster']['name']}-node-pool",
            location=self.config['app_cluster']['zone'],
            cluster=self.cluster.name,
            node_count=self.config['node_pool']['node_count'],

            # Add required version
            version=self.config['node_pool']['node_version'],

            # Complete node configuration
            node_config={
                # Required base configuration
                "machine_type": self.config['node_pool']['app_cluster']['machine_type'],
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
                },
            },

            opts=ResourceOptions(parent=self)
        )