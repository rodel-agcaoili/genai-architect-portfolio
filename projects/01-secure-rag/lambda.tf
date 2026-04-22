# Create the ZIP
data "archive_file" "ingestor_zip" {
  type        = "zip"
  source_dir  = "${path.module}/lambda/ingestor"
  output_path = "${path.module}/lambda/ingestor.zip"
}

resource "aws_lambda_function" "rag_ingestor" {
  filename         = data.archive_file.ingestor_zip.output_path
  function_name    = "rag-ingestor-${random_id.suffix.hex}"
  role             = aws_iam_role.rag_lambda_role.arn
  handler          = "index.lambda_handler"
  runtime          = "python3.12"
  timeout          = 30
  memory_size      = 512

  source_code_hash = data.archive_file.ingestor_zip.output_base64sha256

  layers = [aws_lambda_layer_version.faiss_layer.arn]

  # Increase storage for the /tmp directory
  # FAISS indices can grow, and the default 512MB might be tight
  ephemeral_storage {
    size = 1024 # 1GB of /tmp space
  }

  environment {
    variables = {
      VECTOR_BUCKET_NAME = aws_s3_bucket.vector_store_bucket.id
      # Add the model ID as a variable for easy switching
      EMBEDDING_MODEL_ID = "amazon.titan-embed-text-v2:0"
    }
  }
}
