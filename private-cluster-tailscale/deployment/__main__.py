"""
Main Pulumi program for hungry-echoes application deployments.
This program manages the deployment of application components
on top of the existing GKE infrastructure.
"""
import pulumi
from pulumi import ResourceOptions
from pulumi_kubernetes import Provider as K8sProvider

# Local imports
from k8s.network import NetworkPolicies
from k8s.app import AppDeployment
from k8s.monitoring import MonitoringDeployment
from k8s.postgres import PostgresDeployment
from utils.kubernetes import create_kubeconfig
from utils.global_settings import settings

# Custom exception for initialization failures
class InitializationError(Exception):
    pass

def create_k8s_provider():
    """
    Creates and configures the Kubernetes provider using the cluster details
    from the infrastructure stack.
    """
    try:
        # Get reference to the infrastructure stack
        infra_stack = pulumi.StackReference("pouyan/hungry-echoes/he-infra")

        # Create kubernetes provider using the kubeconfig
        return K8sProvider("k8s",
            kubeconfig=pulumi.Output.all(
                infra_stack.get_output("app_cluster_name"),
                infra_stack.get_output("app_cluster_endpoint"),
                infra_stack.get_output("app_cluster_master_auth")
            ).apply(lambda args: create_kubeconfig(
                cluster_name=args[0],
                endpoint=args[1],
                cluster_ca=args[2]["cluster_ca_certificate"],
                project_id=settings.project_id,
                zone=settings.app_cluster_zone
            ))
        )
    except Exception as e:
        raise InitializationError(f"Failed to create Kubernetes provider: {str(e)}")

def main():
    """
    Main deployment logic with improved error handling and update strategies.
    """
    try:
        # Step 1: Create the Kubernetes provider
        k8s_provider = create_k8s_provider()

        # Step 2: Deploy network policies 
        network = NetworkPolicies(
            "network",
            opts=ResourceOptions(
                provider=k8s_provider,
                custom_timeouts=pulumi.CustomTimeouts(
                    create="10m",
                    update="10m",
                    delete="10m"
                ),
                delete_before_replace=True,
            )
        )

        # Step 3: Deploy PostgreSQL after policies are set up
        postgres = PostgresDeployment(
            "postgres",
            opts=ResourceOptions(
                provider=k8s_provider,
                depends_on=[network],
                custom_timeouts=pulumi.CustomTimeouts(
                    create="15m",
                    update="15m",
                    delete="15m"
                ),
                delete_before_replace=True,
            )
        )

        # Step 4: Deploy the main application after both the network and the database is ready
        app = AppDeployment(
            "app",
            secret_name=postgres.postgres_secret.metadata["name"],
            opts=ResourceOptions(
                provider=k8s_provider,
                depends_on=[network, postgres],
                custom_timeouts=pulumi.CustomTimeouts(
                    create="10m",
                    update="10m",
                    delete="10m"
                ),
                delete_before_replace=True,
            )
        )

        # Step 5: Deploy monitoring configuration
        monitoring = MonitoringDeployment(
            "monitoring",
            opts=ResourceOptions(
                provider=k8s_provider,
                depends_on=[network],
                custom_timeouts=pulumi.CustomTimeouts(
                    create="10m",
                    update="10m",
                    delete="10m"
                ),
                delete_before_replace=True,
            )
        )

        # Export useful information
        # Note: Sensitive information like database credentials should not be exported
        pulumi.export('app_url', "http://hungryechoes.com")
        pulumi.export('metrics_url', "http://metrics.hungryechoes.com")

    except InitializationError as e:
        # Handle initialization failures
        pulumi.log.error(f"Failed to initialize deployment: {str(e)}")
        raise
    except Exception as e:
        # Handle unexpected errors
        pulumi.log.error(f"Unexpected error during deployment: {str(e)}")
        raise

# Only run main() if this is the main module
if __name__ == "__main__":
    main()