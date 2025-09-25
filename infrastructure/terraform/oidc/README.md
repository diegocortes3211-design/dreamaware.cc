# Bootstrap OIDC for GitHub → AWS

1) Edit variables:
   - org = your GitHub org/user (e.g., diegocortes3211-design)
   - repo = your repository (e.g., dreamaware.ai)
   - branch = main (or your default)

2) (Optional) If deploying static assets, set:
   - artifact_bucket_arn = arn:aws:s3:::your-bucket
   - cf_distribution_id  = E123ABC456

3) Apply:
   terraform init
   terraform apply

4) Copy the output role_arn and store it in GitHub → Settings → Secrets and variables → Actions:
   - New Repository Secret: AWS_OIDC_ROLE_ARN = <role_arn>
