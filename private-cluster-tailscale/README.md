## Steps to provision the app cluster
1. Go to ./infra/app-cluster-infra and run the terraform commands to provision the app cluster:
    - terraform init -upgrade
    - terraform plan
    - terraform apply
2. Once the cluster is fully provisioned, go to ./k8s/postgres/secret.yaml and set the password (POSTGRES_PASSWORD) to something that you'd like
3. Run kubectl apply -f ./postgres and then comment out the POSTGRES_PASSOWRD; make sure to remove the password that you used
4. Run kubectl apply -f ./app
5. Go back to ./infra/dns and run the terraform commands to provision the DNS records:
    - terraform init -upgrade
    - terraform plan
    - terraform apply

## Steps to provision the monitoring cluster
1. Go to ./infra/monitoring-cluster-infra and run the terraform commands to provision the monitoring cluster:
    - terraform init -upgrade
    - terraform plan
    - terraform apply
2. Once the cluster is fully provisioned, go to ./k8s
3. Run kubectl apply -f ./monitoring

## Verify DNS settings
Verify that DNS records in the domain registrar is pointing to the right Google name servers (they can change from one run to the next).