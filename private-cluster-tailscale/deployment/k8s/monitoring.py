from pulumi import ComponentResource, ResourceOptions
from pulumi_kubernetes.yaml import ConfigGroup

class MonitoringDeployment(ComponentResource):
    """
    Deploys monitoring components using existing k8s YAML files.
    Primarily manages custom Prometheus configurations.
    """
    
    def __init__(self, name: str, opts: ResourceOptions = None):
        super().__init__('hungry-echoes:k8s:monitoring', name, None, opts)

        # Deploy monitoring namespace and Prometheus configuration
        self.monitoring_components = ConfigGroup(
            "monitoring-deployment",
            files=[
                "../k8s/monitoring/config.yaml",  # Only contains Prometheus config
            ],
            opts=ResourceOptions(parent=self)
        )

        self.register_outputs({})