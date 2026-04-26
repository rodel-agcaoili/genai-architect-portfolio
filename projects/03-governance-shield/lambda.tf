data "archive_file" "proxy_zip" {
  type        = "zip"
  source_dir  = "${path.module}/lambda/proxy"
  output_path = "${path.module}/lambda/proxy.zip"
}

resource "aws_lambda_function" "governance_proxy" {
  function_name    = "sentinel-governance-proxy-${random_id.shield_suffix.hex}"
  role             = aws_iam_role.proxy_lambda_role.arn
  handler          = "index.lambda_handler"
  runtime          = "python3.12"
  filename         = data.archive_file.proxy_zip.output_path
  source_code_hash = data.archive_file.proxy_zip.output_base64sha256
  timeout          = 30

  environment {
    variables = {
      GUARDRAIL_ID      = aws_bedrock_guardrail.enterprise_shield.guardrail_id
      GUARDRAIL_VERSION = aws_bedrock_guardrail_version.v1.version
    }
  }
}

output "governance_proxy_lambda_arn" {
  value       = aws_lambda_function.governance_proxy.arn
  description = "The ARN of the Python PII Regex Proxy."
}
