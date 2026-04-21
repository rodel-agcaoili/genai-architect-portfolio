# Trigger installation of libraries
resource "null_resource" "build_lambda_layer" {
  triggers = {
    requirements_hash = filemd5("${path.module}/../../infrastructure/modules/lambda_layers/faiss_layer/requirements.txt")
  }

  provisioner "local-exec" {
    command = <<EOT
      mkdir -p ${path.module}/python
      pip install -r ${path.module}/../../infrastructure/modules/lambda_layers/faiss_layer/requirements.txt -t ${path.module}/python/ --platform manylinux2014_x86_64 --only-binary=:all:
    EOT
  }
}

# Zip the resulting python folder
data "archive_file" "faiss_layer_zip" {
  type        = "zip"
  source_dir  = "${path.module}/python"
  output_path = "${path.module}/faiss_layer.zip"
  depends_on  = [null_resource.build_lambda_layer]
}

# Create the Lambda Layer
resource "aws_lambda_layer_version" "faiss_layer" {
  filename            = data.archive_file.faiss_layer_zip.output_path
  layer_name          = "faiss_ai_layer"
  compatible_runtimes = ["python3.12"]
  
  # This hash ensures the layer only redeploys if the ZIP changes
  source_code_hash    = data.archive_file.faiss_layer_zip.output_base64sha256
}
