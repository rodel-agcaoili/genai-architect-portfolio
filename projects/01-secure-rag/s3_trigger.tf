resource "aws_lambda_permission" "allow_s3_to_call_ingestor" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.rag_ingestor.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.data_landing_zone.arn
}

resource "aws_s3_bucket_notification" "on_upload_trigger" {
  bucket = aws_s3_bucket.data_landing_zone.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.rag_ingestor.arn
    events              = ["s3:ObjectCreated:*"]
    filter_suffix       = ".txt" # Filters for text files
  }

  depends_on = [aws_lambda_permission.allow_s3_to_call_ingestor]
}
