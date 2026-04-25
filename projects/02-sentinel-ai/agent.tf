# -----------------------------------------------------------------------------------------
# "I encapsulated the Bedrock Agent as Infrastructure-as-Code. This enables declarative
# deployment of our cognitive logic. The Agent is directly tied to the OpenAPI schema 
# defined locally, mapping intents to actionable serverless lambdas. This orchestration
# ensures our agentic workflows are version-controlled, auditable, and resilient."
# -----------------------------------------------------------------------------------------

resource "aws_bedrockagent_agent" "sentinel_agent" {
  agent_name       = "sentinel-security-agent"
  foundation_model = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"

  instruction = <<EOT
    You are SentinelAI, a Senior Security Auditor for the AWS Generative AI Platform.
    Your primary goal is to identify and remediate security misconfigurations, specifically 
    focusing on AWS S3 buckets.
    
    You have access to an Action Group allowing you to Audit S3 Buckets and Secure them.
    Before securing any bucket, explicitly explain to the user WHY the bucket needs securing.
    Never take action without explicitly confirming with the user context.
  EOT

  description                 = "Autonomous security remediation agent using Human-in-the-Loop workflows."
  idle_session_ttl_in_seconds = 1800
  agent_resource_role_arn     = aws_iam_role.bedrock_agent_role.arn
}

resource "aws_bedrockagent_agent_action_group" "s3_auditor" {
  action_group_name          = "S3SecurityActionGroup"
  agent_id                   = aws_bedrockagent_agent.sentinel_agent.id
  agent_version              = "DRAFT"
  skip_resource_in_use_check = true

  action_group_executor {
    # Dynamically inject the ARN of the Lambda we deployed
    lambda = aws_lambda_function.agent_remediator.arn
  }

  api_schema {
    # Dynamically inject the OpenAPI spec
    payload = file("${path.module}/schema.json")
  }
}

# The Lambda deployment (Assumes the python file is zipped into remediator.zip)
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/lambda/agent"
  output_path = "${path.module}/remediator.zip"
}

resource "aws_lambda_function" "agent_remediator" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "SentinelAI-S3Remediator"
  role             = aws_iam_role.lambda_exec_role.arn
  handler          = "remediator.lambda_handler"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime          = "python3.12"
  timeout          = 30
}

# Basic execution role for the lambda itself
resource "aws_iam_role" "lambda_exec_role" {
  name = "sentinel-lambda-exec-role"
  assume_role_policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [{ Action = "sts:AssumeRole", Effect = "Allow", Principal = { Service = "lambda.amazonaws.com" } }]
  })
}

resource "aws_iam_role_policy" "lambda_s3_policy" {
  name = "sentinel-lambda-s3-policy"
  role = aws_iam_role.lambda_exec_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["s3:ListAllMyBuckets", "s3:GetBucketPublicAccessBlock", "s3:PutBucketPublicAccessBlock"]
        Effect   = "Allow"
        Resource = "*"
      }
    ]
  })
}
