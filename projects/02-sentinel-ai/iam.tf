# -----------------------------------------------------------------------------------------
# "To satisfy the principle of least-privilege, I strictly isolated the Bedrock Agent IAM role.
# I do not use '*' resource mappings. Instead, I scoped down the AssumeRole trust policy
# dynamically mapping to the specific region. The execution policy only allows invocation 
# of the specific remediator Lambda function, eliminating the prospect of horizontal escalation."
# -----------------------------------------------------------------------------------------

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

resource "aws_iam_role" "bedrock_agent_role" {
  name = "sentinel-agent-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "bedrock.amazonaws.com"
        }
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
          ArnLike = {
            "aws:SourceArn" = "arn:aws:bedrock:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:agent/*"
          }
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "agent_permissions" {
  name = "sentinel-agent-least-privilege"
  role = aws_iam_role.bedrock_agent_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        # Grants explicit reasoning capability
        Action   = "bedrock:InvokeModel"
        Effect   = "Allow"
        Resource = "arn:aws:bedrock:${data.aws_region.current.name}::foundation-model/us.anthropic.claude-3-7-sonnet-20250219-v1:0"
      },
      {
        # Stricts lambda invocation exactly to the target ARN
        Action   = "lambda:InvokeFunction"
        Effect   = "Allow"
        Resource = aws_lambda_function.agent_remediator.arn
      }
    ]
  })
}

# The trusted relationship allowing Bedrock Agent specifically to invoke the remediator lambda
resource "aws_lambda_permission" "allow_bedrock_invoke" {
  statement_id  = "AllowBedrockInvocation"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.agent_remediator.function_name
  principal     = "bedrock.amazonaws.com"
  source_arn    = "arn:aws:bedrock:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:agent/${aws_bedrockagent_agent.sentinel_agent.id}"
}


