data "archive_file" "query_zip" {
  type        = "zip"
  source_dir  = "${path.module}/lambda/query"
  output_path = "${path.module}/lambda/query.zip"
}

resource "aws_lambda_function" "rag_query" {
  filename         = data.archive_file.query_zip.output_path
  function_name    = "rag-query-${random_id.suffix.hex}"
  role             = aws_iam_role.rag_lambda_role.arn
  handler          = "index.lambda_handler"
  runtime          = "python3.12"
  timeout          = 60
  memory_size      = 1024 # More RAM for Claude's payload and FAISS search

  # Reuse the layer built in layers.tf
  layers = [aws_lambda_layer_version.faiss_layer.arn]

  environment {
    variables = {
      VECTOR_BUCKET_NAME = aws_s3_bucket.vector_store_bucket.id
    }
  }
}
