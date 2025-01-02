# app_cluster/ingress.py

from pulumi import ComponentResource, ResourceOptions, runtime
from pulumi_kubernetes.helm.v3 import Chart, ChartOpts
from pulumi_kubernetes.core.v1 import Namespace
import os

class AppClusterAddons(ComponentResource):
    """
    Installs required Helm charts (NGINX Ingress and Tailscale) on the GKE cluster.
    Includes logic to skip Helm deployments during the Pulumi preview phase.
    """

    def __init__(self, name: str, opts: ResourceOptions = None):
        super().__init__('hungry-echoes:addons', name, None, opts)

        # Create namespace for NGINX Ingress
        self.nginx_namespace = Namespace(
            "nginx-namespace",
            metadata={
                "name": "ingress-nginx"
            },
            opts=ResourceOptions(parent=self)
        )

        # Deploy NGINX Ingress Controller only during apply phase
        if not runtime.is_dry_run():
            # Install NGINX Ingress Controller
            self.nginx_ingress = Chart(
                "nginx-ingress",
                ChartOpts(
                    chart="ingress-nginx",
                    version="4.11.3",
                    fetch_opts={
                        "repo": "https://kubernetes.github.io/ingress-nginx"
                    },
                    namespace=self.nginx_namespace.metadata["name"],
                    values={
                        "controller": {
                            "replicaCount": 1,
                            "service": {
                                "type": "LoadBalancer"
                            },
                            "resources": {
                                "requests": {
                                    "memory": "64Mi",
                                    "cpu": "100m"
                                },
                                "limits": {
                                    "memory": "128Mi",
                                    "cpu": "200m"
                                }
                            }
                        }
                    }
                ),
                opts=ResourceOptions(parent=self, depends_on=[self.nginx_namespace])
            )
        else:
            print("Skipping NGINX Ingress deployment during preview.")

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
            app_tailscale_client_id = os.getenv('APP_TAILSCALE_OAUTH_CLIENT_ID')
            app_tailscale_client_secret = os.getenv('APP_TAILSCALE_OAUTH_CLIENT_SECRET')

            if not app_tailscale_client_id or not app_tailscale_client_secret:
                raise ValueError(
                    "APP_TAILSCALE_OAUTH_CLIENT_ID and APP_TAILSCALE_OAUTH_CLIENT_SECRET "
                    "environment variables must be set"
                )

            # Install Tailscale Operator
            self.tailscale = Chart(
                "tailscale",
                ChartOpts(
                    chart="tailscale-operator",
                    fetch_opts={
                        "repo": "https://pkgs.tailscale.com/helmcharts/"
                    },
                    namespace=self.tailscale_namespace.metadata["name"],
                    values={
                        "oauth": {
                            "clientId": app_tailscale_client_id,
                            "clientSecret": app_tailscale_client_secret
                        },
                        "operator": {
                            "hostname": "app-tailscale-operator"
                        }
                    }
                ),
                opts=ResourceOptions(parent=self, depends_on=[self.tailscale_namespace])
            )
        else:
            print("Skipping Tailscale deployment during preview.")

        # Register outputs
        self.register_outputs({})