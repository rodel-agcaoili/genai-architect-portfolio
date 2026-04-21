resource "aws_s3_bucket" "data_landing_zone" {
  bucket_prefix = "rag-data-ingest-"
  force_destroy = true
}

# Enable encryption by default
resource "aws_s3_bucket_server_side_encryption_configuration" "s3_encryption" {
  bucket = aws_s3_bucket.data_landing_zone.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
