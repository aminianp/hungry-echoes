# app_cluster/utils/kubernetes.py
import yaml
from typing import Dict, Any

def create_kubeconfig_from_promise(args, project_id, zone):
    return create_kubeconfig(
                    cluster_name=args[0],
                    endpoint=args[1],
                    cluster_ca=args[2]["cluster_ca_certificate"],
                    project_id=project_id,
                    zone=zone
                )

def create_kubeconfig(cluster_name: str, endpoint: str, cluster_ca: str, project_id: str, zone: str) -> str:
    """
    Creates a kubeconfig string for GKE cluster authentication using the new
    gke-gcloud-auth-plugin.
    
    Args:
        cluster_name: Name of the GKE cluster
        endpoint: Cluster API server endpoint
        cluster_ca: Cluster CA certificate data
        project_id: GCP project ID
        zone: GCP zone where cluster is located
        
    Returns:
        A YAML string containing the kubeconfig
    """
    return yaml.dump(_build_kubeconfig_dict(
        cluster_name, endpoint, cluster_ca, project_id, zone))

def _build_kubeconfig_dict(cluster_name: str, endpoint: str, cluster_ca: str,
                          project_id: str, zone: str) -> Dict[str, Any]:
    """
    Builds the kubeconfig dictionary structure with the new GKE auth plugin.
    
    This implementation uses the gke-gcloud-auth-plugin which is the new
    standard for GKE authentication as of 2023.
    """
    context_name = f"gke_{project_id}_{zone}_{cluster_name}"
    return {
        "apiVersion": "v1",
        "kind": "Config",
        "current-context": context_name,
        "preferences": {},
        "clusters": [{
            "name": context_name,
            "cluster": {
                "certificate-authority-data": cluster_ca,
                "server": f"https://{endpoint}"
            }
        }],
        "contexts": [{
            "name": context_name,
            "context": {
                "cluster": context_name,
                "user": context_name
            }
        }],
        "users": [{
            "name": context_name,
            "user": {
                "exec": {
                    "apiVersion": "client.authentication.k8s.io/v1beta1",
                    "command": "gke-gcloud-auth-plugin",
                    "provideClusterInfo": True,
                }
            }
        }]
    }