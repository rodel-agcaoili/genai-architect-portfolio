# Upload the ZIP to S3 instead of sending it via API
resource "aws_s3_object" "faiss_layer_artifact" {
  bucket = aws_s3_bucket.vector_store_bucket.id
  key    = "artifacts/faiss_layer_${random_id.suffix.hex}.zip"
  source = data.archive_file.faiss_layer_zip.output_path
  
  # Ensure the ZIP is rebuilt before uploading
  depends_on = [data.archive_file.faiss_layer_zip]
}

# Update the Layer to point to the S3 Object
resource "aws_lambda_layer_version" "faiss_layer" {
  layer_name = "faiss_ai_layer-${random_id.suffix.hex}"
  
  s3_bucket = aws_s3_bucket.vector_store_bucket.id
  s3_key    = aws_s3_object.faiss_layer_artifact.key
  
  compatible_runtimes = ["python3.12"]
  
  # Keeps the layer updated if the zip content changes
  source_code_hash = data.archive_file.faiss_layer_zip.output_base64sha256
}