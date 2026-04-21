resource "aws_s3_bucket" "vector_store_bucket" {
  bucket_prefix = "rag-vector-store-"
  force_destroy = true
}

# Separate the 'Metadata' from the 'Vectors'
resource "aws_s3_object" "index_folder" {
  bucket = aws_s3_bucket.vector_store_bucket.id
  key    = "indices/"
}

output "vector_store_bucket_name" {
  value = aws_s3_bucket.vector_store_bucket.id
}
