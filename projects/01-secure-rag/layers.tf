data "archive_file" "faiss_layer_zip" {
  type        = "zip"
  source_dir  = "${path.module}/layer_build"
  output_path = "${path.module}/faiss_layer.zip"
  depends_on  = [null_resource.build_lambda_layer]
}

resource "aws_lambda_layer_version" "faiss_layer" {
  filename            = data.archive_file.faiss_layer_zip.output_path
  layer_name          = "faiss_ai_layer-${random_id.suffix.hex}" # Added random suffix for clean redeploys
  compatible_runtimes = ["python3.12"]
  source_code_hash    = data.archive_file.faiss_layer_zip.output_base64sha256
}
