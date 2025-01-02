from pulumi import ComponentResource, ResourceOptions, runtime
from pulumi_kubernetes.helm.v3 import Chart, ChartOpts
from pulumi_kubernetes.core.v1 import Namespace
import os

class MonitoringClusterAddons(ComponentResource):
    """
    Installs monitoring components (Prometheus) on the GKE monitoring cluster
    using Helm charts for easier management and updates.
    """

    def __init__(self, name: str, opts: ResourceOptions = None):
        super().__init__('hungry-echoes:monitoring-addons', name, None, opts)

        # Create monitoring namespace
        self.monitoring_namespace = Namespace(
            "monitoring-namespace",
            metadata={
                "name": "monitoring"
            },
            opts=ResourceOptions(parent=self)
        )

        #### Opted for a simpler deployment via static manifests; will revisit this if needed!

        # # Deploy Prometheus only during apply phase
        # if not runtime.is_dry_run():
        #     # Install Prometheus using the kube-prometheus-stack Helm chart
        #     # This chart includes Prometheus, Alertmanager, and necessary CRDs
        #     self.prometheus = Chart(
        #         "prometheus",
        #         ChartOpts(
        #             chart="kube-prometheus-stack",  # Changed from prometheus to kube-prometheus-stack
        #             version="51.9.3",  # Updated version
        #             fetch_opts={
        #                 "repo": "https://prometheus-community.github.io/helm-charts"
        #             },
        #             namespace=self.monitoring_namespace.metadata["name"],
        #             values={
        #                 # Configure Prometheus server
        #                 "prometheus": {
        #                     "prometheusSpec": {
        #                         "resources": {
        #                             "requests": {
        #                                 "cpu": "500m",
        #                                 "memory": "500Mi"
        #                             },
        #                             "limits": {
        #                                 "cpu": "1",
        #                                 "memory": "1Gi"
        #                             }
        #                         },
        #                         # Configure remote write for your metrics
        #                         "remoteWrite": [{
        #                             "url": "${REMOTE_WRITE_URL}",  # You'll need to set this
        #                             "writeRelabelConfigs": [{
        #                                 "sourceLabels": ["__name__"],
        #                                 "regex": "hungry_echoes_.*",  # Only send your app metrics
        #                                 "action": "keep"
        #                             }]
        #                         }]
        #                     }
        #                 },
        #                 # Disable components we don't need for this demo
        #                 "alertmanager": {
        #                     "enabled": False
        #                 },
        #                 "grafana": {
        #                     "enabled": False
        #                 },
        #                 "nodeExporter": {
        #                     "enabled": False
        #                 },
        #                 "kubeStateMetrics": {
        #                     "enabled": True
        #                 }
        #             }
        #         ),
        #         opts=ResourceOptions(parent=self, depends_on=[self.monitoring_namespace])
        #     )
        # else:
        #     print("Skipping Prometheus deployment during preview.")

        # Create namespace for Tailscale
        self.tailscale_namespace = Namespace(
            "tailscale-namespace",
            metadata={
                "name": "tailscale"
            },
            opts=ResourceOptions(parent=self)
        )

        # Deploy Tailscale Operator only during apply phase
        if not runtime.is_dry_run():
            # Fetch Tailscale OAuth credentials from environment variables
            monitoring_tailscale_client_id = os.getenv('MONITORING_TAILSCALE_OAUTH_CLIENT_ID')
            monitoring_tailscale_client_secret = os.getenv('MONITORING_TAILSCALE_OAUTH_SECRET')

            if not monitoring_tailscale_client_id or not monitoring_tailscale_client_secret:
                raise ValueError(
                    "MONITORING_TAILSCALE_OAUTH_CLIENT_ID and MONITORING_TAILSCALE_OAUTH_SECRET "
                    "environment variables must be set"
                )


        if not runtime.is_dry_run():
            # Install Tailscale Operator
            self.tailscale = Chart(
                "tailscale-monitoring",  
                ChartOpts(
                    chart="tailscale-operator",
                    fetch_opts={
                        "repo": "https://pkgs.tailscale.com/helmcharts/"
                    },
                    namespace=self.tailscale_namespace.metadata["name"],
                    values={
                        "oauth": {
                            "clientId": monitoring_tailscale_client_id,
                            "clientSecret": monitoring_tailscale_client_secret
                        },
                        "operator": {
                            "hostname": "monitoring-tailscale-operator"
                        }
                    }
                ),
                opts=ResourceOptions(parent=self, depends_on=[self.tailscale_namespace])
            )

        self.register_outputs({})