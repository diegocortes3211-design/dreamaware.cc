# Bootstrap OIDC for GitHub → AWS

This Terraform configuration sets up a secure, passwordless trust between your GitHub repository and your AWS account using an OpenID Connect (OIDC) provider. This allows GitHub Actions workflows to assume an IAM role and access AWS resources without needing long-lived static credentials.

## One-Time Manual Setup

The initial creation of the OIDC provider and the IAM role is a one-time setup that **must be performed manually from a trusted local environment** where you have securely configured AWS credentials (e.g., via `aws configure`).

### Prerequisites

1.  **Terraform CLI:** Ensure you have the Terraform CLI installed locally.
2.  **AWS Credentials:** Configure your AWS CLI with credentials that have sufficient permissions to create IAM resources (OIDC providers, roles, policies).

### Steps

1.  **Navigate to the Terraform directory:**
    ```bash
    cd infrastructure/terraform/oidc
    ```

2.  **Initialize Terraform:**
    ```bash
    terraform init
    ```

3.  **Apply the Terraform Configuration:**
    Run the `apply` command, passing your specific repository details as variables. This is the most secure way to provide these values without hardcoding them.

    ```bash
    terraform apply \
      -var="org=your-github-org" \
      -var="repo=your-github-repo" \
      -var="branch=main"
    ```
    *   Replace `your-github-org` and `your-github-repo` with your actual GitHub organization/user and repository name.
    *   If you are using a different default branch, update the `branch` variable accordingly.

4.  **Capture the Output and Configure GitHub Secrets:**
    After the `apply` command completes successfully, Terraform will output a `role_arn`. You need to add this ARN and your AWS region as secrets to your GitHub repository so that subsequent CI/CD workflows can use them.

    Navigate to your GitHub repository and go to **Settings → Secrets and variables → Actions**. Create the following two repository secrets:

    *   `AWS_OIDC_ROLE_ARN`: Copy and paste the `role_arn` value from the Terraform output.
    *   `AWS_REGION`: Enter the AWS region you are using (e.g., `us-east-1`).

Once this one-time manual setup is complete, the `validate-infra.yml` workflow will be able to run on pull requests, using the OIDC role to authenticate securely.