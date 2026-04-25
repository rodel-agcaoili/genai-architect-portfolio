# -----------------------------------------------------------------------------------------
# Dynamic Testing Resources
# Since ACloudGuru Sandbox accounts start completely empty, we need some explicitly 
# "vulnerable" S3 buckets created alongside our agent. These buckets will deliberately 
# NOT have Public Access Blocks applied, giving SentinelAI something to hunt down and fix!
# -----------------------------------------------------------------------------------------

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "vulnerable_alpha" {
  bucket        = "sentinel-insecure-alpha-${random_id.bucket_suffix.hex}"
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "vulnerable_alpha_pab" {
  bucket = aws_s3_bucket.vulnerable_alpha.id

  block_public_acls       = false
  ignore_public_acls      = false
  block_public_policy     = false
  restrict_public_buckets = false
}

resource "aws_s3_bucket" "vulnerable_beta" {
  bucket        = "sentinel-insecure-beta-${random_id.bucket_suffix.hex}"
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "vulnerable_beta_pab" {
  bucket = aws_s3_bucket.vulnerable_beta.id

  block_public_acls       = false
  ignore_public_acls      = false
  block_public_policy     = false
  restrict_public_buckets = false
}

# The Lambda script specifically looks for buckets missing a PublicAccessBlockConfiguration.
# By creating these bare buckets, we purposefully trigger the 'INSECURE' state.
