# Deploy NGINX ingress controller
resource "helm_release" "nginx_ingress" {
  name             = "ingress-nginx"
  namespace        = "ingress-nginx"
  repository       = "https://kubernetes.github.io/ingress-nginx"
  chart            = "ingress-nginx"
  version          = "4.11.3"
  create_namespace = true

  values = [<<EOF
controller:
  replicaCount: 2
  service:
    type: LoadBalancer
  resources:
    requests:
      memory: "64Mi"
      cpu: "100m"
    limits:
      memory: "128Mi"
      cpu: "200m"
EOF
  ]

  # Make sure cluster is ready before installing
  depends_on = [
    google_container_cluster.cluster
  ]
}