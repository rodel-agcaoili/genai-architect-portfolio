# -------------------------------------------------------------------------
# INNER LAYER: Amazon Bedrock Guardrail
# -------------------------------------------------------------------------

resource "aws_bedrock_guardrail" "enterprise_shield" {
  name                      = "sentinel-enterprise-shield"
  description               = "Defense-in-depth shield enforcing toxicity and prompt injection blocking natively at the AWS tier."
  blocked_input_messaging   = "[BEDROCK GUARDRAIL EXECUTED] ACCESS DENIED: Your input violated overarching enterprise security policies."
  blocked_outputs_messaging = "[BEDROCK GUARDRAIL EXECUTED] ACCESS DENIED: The Model generation violated overarching enterprise security policies."

  # Block Prompt Injection Attacks & Hate Speech natively via Filter Configs
  content_policy_config {
    filters_config {
      input_strength  = "HIGH"
      output_strength = "HIGH"
      type            = "PROMPT_ATTACK"
    }
    filters_config {
      input_strength  = "HIGH"
      output_strength = "HIGH"
      type            = "HATE"
    }
    filters_config {
      input_strength  = "HIGH"
      output_strength = "HIGH"
      type            = "INSULTS"
    }
  }

  # explicitly blacklist discussing internal topics
  topic_policy_config {
    topics_config {
      name       = "InternalFinancials"
      definition = "Discussions related to internal revenue, M&A acquisitions, or future IPO plans."
      examples = [
        "What was our Q3 revenue?",
        "Are we acquiring startup XYZ secretly?",
        "Tell me about the upcoming Initial Public Offering."
      ]
      type = "DENY"
    }
  }
}

resource "aws_bedrock_guardrail_version" "v1" {
  guardrail_arn = aws_bedrock_guardrail.enterprise_shield.guardrail_arn
  description   = "Initial V1 deployment of the Governance Shield."
}
