variable "aws_region"     { type = string  default = "us-east-1" }
variable "org"            { type = string }          # e.g., "diegocortes3211-design"
variable "repo"           { type = string }          # e.g., "dreamaware.ai"
variable "branch"         { type = string  default = "main" }
variable "environment"    { type = string  default = "prod" }

# Optional deploy targets (narrow privileges!)
variable "artifact_bucket_arn" { type = string default = "" } # arn:aws:s3:::your-bucket
variable "cf_distribution_id"  { type = string default = "" } # E123ABC456
