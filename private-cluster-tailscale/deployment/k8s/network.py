from pulumi import ComponentResource, ResourceOptions
from pulumi_kubernetes.yaml import ConfigGroup

class NetworkPolicies(ComponentResource):
    """
    Deploys base network policies that should exist before
    any application components are deployed.
    """
    
    def __init__(self, name: str, opts: ResourceOptions = None):
        super().__init__('hungry-echoes:k8s:network', name, None, opts)

        # Deploy all network policies
        self.network_policies = ConfigGroup(
            "network-policies",
            files=[
                "../k8s/network/base-policies.yaml",
            ],
            opts=ResourceOptions(parent=self)
        )

        self.register_outputs({})