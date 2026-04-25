#!/bin/bash
# -----------------------------------------------------------------------------------------
# PRINCIPAL's NARRATIVE:
# "To handle the ephemeral nature of Pluralsight/ACloudGuru sandbox environments, 
# I developed this operational script. It securely extracts temporary AWS IAM tokens
# from the local terminal environment and seamlessly injects them into GitHub Actions Secrets.
# This avoids hardcoding credentials and significantly accelerates the 'Time-to-Demo' loop."
# -----------------------------------------------------------------------------------------

echo "Syncing temporary AWS Lab credentials to GitHub Actions..."

if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ] || [ -z "$AWS_SESSION_TOKEN" ]; then
  echo "❌ Error: AWS Credentials not found in environment."
  echo "Please export AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_SESSION_TOKEN first."
  echo "Example:"
  echo 'export AWS_ACCESS_KEY_ID="ASIA..."'
  echo 'export AWS_SECRET_ACCESS_KEY="wJalr..."'
  echo 'export AWS_SESSION_TOKEN="IQoJb3..."'
  exit 1
fi

# Use GitHub CLI to securely set repo secrets
gh secret set AWS_ACCESS_KEY_ID --body "$AWS_ACCESS_KEY_ID"
echo "✅ AWS_ACCESS_KEY_ID updated."

gh secret set AWS_SECRET_ACCESS_KEY --body "$AWS_SECRET_ACCESS_KEY"
echo "✅ AWS_SECRET_ACCESS_KEY updated."

gh secret set AWS_SESSION_TOKEN --body "$AWS_SESSION_TOKEN"
echo "✅ AWS_SESSION_TOKEN updated."

echo "🎉 Success! Your GitHub Actions pipeline now has the latest ephemeral lab credentials."
