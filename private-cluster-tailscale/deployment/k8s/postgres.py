from pulumi import ComponentResource, ResourceOptions, Config, Output
from pulumi_kubernetes.yaml import ConfigGroup
from pulumi_kubernetes.core.v1 import Secret

class PostgresDeployment(ComponentResource):
    """
    Deploys PostgreSQL components using existing k8s YAML files.
    Includes ConfigMap, Secret, NetworkPolicy, and StatefulSet.
    """
    
    def __init__(self, name: str, opts: ResourceOptions = None):
        super().__init__('hungry-echoes:k8s:postgres', name, None, opts)

        # Initialize config
        config = Config()
        
        # Try to get existing password or prompt for a new one
        # The decrypt=True parameter means Pulumi will automatically decrypt 
        # the secret if it exists in the state
        postgres_password = config.get_secret("postgres_password")
        if not postgres_password:
            # If password doesn't exist, Pulumi will prompt during deployment
            postgres_password = config.require_secret("postgres_password")

        # Create PostgreSQL secret
        self.postgres_secret = Secret(
            "postgres-secret",
            metadata={
                "name": "postgres-secret"
            },
            string_data={
                "POSTGRES_USER": "he-user",
                "POSTGRES_PASSWORD": postgres_password,
                "POSTGRES_DB": "phrases"
            },
            opts=ResourceOptions(parent=self)
        )

        # Deploy other PostgreSQL components
        self.postgres_components = ConfigGroup(
            "postgres-deployment",
            files=[
                "../k8s/postgres/configmap.yaml",
                "../k8s/postgres/network-policy.yaml",
                "../k8s/postgres/statefulset.yaml"  # Note: removed secret.yaml
            ],
            opts=ResourceOptions(
                parent=self,
                depends_on=[self.postgres_secret]  # Ensure secret exists first
            )
        )

        # Register outputs including secret name for other components to use
        self.register_outputs({
            "secret_name": self.postgres_secret.metadata["name"]
        })