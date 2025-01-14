"""
Main Pulumi program for hungry-echoes infrastructure with improved error handling
and update strategies.
"""
import yaml
import os
import pulumi
from pulumi_gcp import Provider as GCPProvider
from pulumi_kubernetes import Provider as K8sProvider
from pulumi import automation as auto

# Local imports
from networking.network import Network
from app_cluster.app_cluster import AppCluster
from app_cluster.app_cluster_add_ons import AppClusterAddons
from monitoring_cluster.monitoring_cluster import MonitoringCluster
from monitoring_cluster.monitoring_cluster_add_ons import MonitoringClusterAddons
from utils.kubernetes import create_kubeconfig_from_promise

# Custom exception for initialization failures
class InitializationError(Exception):
    pass

def create_gcp_provider(config, timeout="120s", gcp_provider_name="gcp-provider"):
    """
    Creates and configures the GCP provider with proper error handling.
    Returns tuple of (gcp_provider, project_id)
    """
    try:
        # Configure the GCP provider with project settings
        gcp_provider = GCPProvider(gcp_provider_name,
            project=config['project']['id'],
            # Add retry configurations for API calls
            request_timeout=timeout,  # Increase timeout for API calls
        )
        return gcp_provider
    except Exception as e:
        raise InitializationError(f"Failed to create GCP provider: {str(e)}")

def create_kube_provider(app_cluster, project_id, zone, kube_provider_name):
    """
    Creates the Kubernetes provider with proper error handling and retry logic.
    """
    
    try:
        kubeconfig = pulumi.Output.all(
                app_cluster.cluster.name, 
                app_cluster.cluster.endpoint, 
                app_cluster.cluster.master_auth
            ).apply(lambda args: create_kubeconfig_from_promise(args, project_id, zone))
        return K8sProvider(kube_provider_name, kubeconfig)

    except Exception as e:
        raise InitializationError(f"Failed to create Kubernetes provider: {str(e)}")

def main():
    """
    Main deployment logic with improved error handling and update strategies.
    """
    # Load global config
    try:
        config_path = os.path.join(os.path.dirname(__file__), './settings.yaml')
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        raise InitializationError(f"Failed to open the settings file at {str(config_path)}. Additional info: {str(e)}")

    try:
        # Step 1: Create the GCP provider
        gcp_provider = create_gcp_provider(config)

        # Step 2: Create shared network infrastructure
        custom_opts = pulumi.ResourceOptions(
                provider=gcp_provider,
                # Add custom timeouts for network operations
                custom_timeouts=pulumi.CustomTimeouts(
                    create="30m",
                    update="30m",
                    delete="30m"
                ),
                # Add proper deletion strategy
                delete_before_replace=True,
            )
        network = Network(config, opts=custom_opts)

        # Step 3: Create app cluster using network configuration
        custom_opts =pulumi.ResourceOptions(
                provider=gcp_provider,
                depends_on=[network],
                # Add custom timeouts for cluster operations
                custom_timeouts=pulumi.CustomTimeouts(
                    create="45m",
                    update="45m",
                    delete="45m"
                ),
                # Ensure proper cleanup on failure
                delete_before_replace=True,
            ) 
        app_cluster = AppCluster(
            config['pulumi_provider']['app_cluster_provider_name'],
            vpc_id=network.vpc.id,
            subnet_id=network.app_subnet.id,
            opts=custom_opts
        )

        # Step 4: Create k8s provider with proper error handling
        app_k8s_provider = create_kube_provider(
            app_cluster,
            config['project']['id'],
            config['app_cluster']['zone'],
            config['pulumi_provider']['app_cluster_k8s_provider_name']
        )

        # Step 5: Install cluster add-ons with improved dependency management
        custom_opts = pulumi.ResourceOptions(
                provider=app_k8s_provider,
                depends_on=[network, app_cluster],
                # Add custom timeouts for add-on operations
                custom_timeouts=pulumi.CustomTimeouts(
                    create="20m",
                    update="20m",
                    delete="20m"
                ),
                # Ensure proper cleanup
                delete_before_replace=True,
                # Add ignore_changes for specific fields that cause unnecessary updates
                ignore_changes=["metadata.annotations", "metadata.labels"]
            )
        app_addons = AppClusterAddons(
            config['pulumi_provider']['app_addons_provider_name'],
            opts=custom_opts
        )

        # Step 6: Create monitoring cluster with proper error handling
        custom_opts = pulumi.ResourceOptions(
                provider=gcp_provider,
                depends_on=[network],
                # Add custom timeouts
                custom_timeouts=pulumi.CustomTimeouts(
                    create="45m",
                    update="45m",
                    delete="45m"
                ),
                # Ensure proper cleanup
                delete_before_replace=True,
            ) 
        monitoring_cluster = MonitoringCluster(
            config['pulumi_provider']['monitoring_cluster_provider_name'],
            vpc_id=network.vpc.id,
            subnet_id=network.monitoring_subnet.id,
            opts = custom_opts
        )

        # Step 7: Create Kubernetes provider for monitoring cluster
        monitoring_k8s_provider = create_kube_provider(
            monitoring_cluster,
            config['project']['id'],
            config['monitoring_cluster']['zone'],
            config['pulumi_provider']['monitoring_cluster_k8s_provider_name']
        )

        # Step 8: Install monitoring cluster add-ons (Prometheus Stack)
        monitoring_addons = MonitoringClusterAddons(
            config['pulumi_provider']['monitoring_addons_provider_name'],
            opts=pulumi.ResourceOptions(
                provider=monitoring_k8s_provider,
                depends_on=[network, monitoring_cluster],
                # Add custom timeouts for add-on operations
                custom_timeouts=pulumi.CustomTimeouts(
                    create="20m",
                    update="20m",
                    delete="20m"
                ),
                # Ensure proper cleanup
                delete_before_replace=True,
                # Add ignore_changes for specific fields that cause unnecessary updates
                ignore_changes=["metadata.annotations", "metadata.labels"]
            )
        )

        # Export necessary values with proper error handling
        pulumi.export('app_cluster_name', app_cluster.cluster.name)
        pulumi.export('app_cluster_endpoint', app_cluster.cluster.endpoint)
        pulumi.export('monitoring_cluster_name', monitoring_cluster.cluster.name)
        pulumi.export('monitoring_cluster_endpoint', monitoring_cluster.cluster.endpoint)
        pulumi.export('vpc_name', network.vpc.name)
        pulumi.export('vpc_id', network.vpc.id)

    except InitializationError as e:
        # Handle initialization failures
        pulumi.log.error(f"Failed to initialize infrastructure: {str(e)}")
        raise
    except Exception as e:
        # Handle unexpected errors
        pulumi.log.error(f"Unexpected error during deployment: {str(e)}")
        raise

# Only run main() if this is the main module
if __name__ == "__main__":
    main()