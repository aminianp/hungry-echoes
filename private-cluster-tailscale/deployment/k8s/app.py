from pulumi import ComponentResource, ResourceOptions, Output
from pulumi_kubernetes.yaml import ConfigGroup

class AppDeployment(ComponentResource):
    """
    Deploys the main application components using existing k8s YAML files.
    Includes Deployment, Service, Ingress, and NetworkPolicy.
    """
    
    def __init__(self, name: str, secret_name: Output[str], opts: ResourceOptions = None):
        super().__init__('hungry-echoes:k8s:app', name, None, opts)

        # Deploy all application components
        self.app_components = ConfigGroup(
            "app-deployment",
            files=[
                "../k8s/app/deployment.yaml",
                "../k8s/app/ingress-app.yaml",
                "../k8s/app/ingress-metrics.yaml",
                "../k8s/app/network-policy.yaml",
                "../k8s/app/service.yaml"
            ],
            transforms=[self.transform_secret_name(secret_name)],
            opts=ResourceOptions(parent=self)
        )

        self.register_outputs({})

    def transform_secret_name(self, secret_name: Output[str]):
        def transformer(obj):
            if obj["kind"] == "Deployment":
                containers = obj["spec"]["template"]["spec"]["containers"]
                for container in containers:
                    for env in container.get("env", []):
                        if env.get("valueFrom", {}).get("secretKeyRef", {}).get("name") == "postgres-secret":
                            env["valueFrom"]["secretKeyRef"]["name"] = secret_name
            return obj
        return transformer