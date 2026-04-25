#!/bin/bash

echo "Syncing temporary AWS Lab credentials to GitHub Actions..."

read -p "Enter AWS_ACCESS_KEY_ID: " AWS_ACCESS_KEY_ID
read -s -p "Enter AWS_SECRET_ACCESS_KEY: " AWS_SECRET_ACCESS_KEY
echo ""
read -s -p "Enter AWS_SESSION_TOKEN (if using temporary lab credentials, otherwise leave blank): " AWS_SESSION_TOKEN
echo ""

if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
  echo "❌ Error: Access Key and Secret Key are required."
  exit 1
fi

# Update Local AWS CLI Credentials
aws configure set aws_access_key_id "$AWS_ACCESS_KEY_ID"
aws configure set aws_secret_access_key "$AWS_SECRET_ACCESS_KEY"
aws configure set region "us-east-1"
if [ -n "$AWS_SESSION_TOKEN" ]; then
  aws configure set aws_session_token "$AWS_SESSION_TOKEN"
else
  aws configure set aws_session_token ""
fi
echo "✅ Local ~/.aws/credentials profile heavily synced!"

# Use GitHub CLI to securely set repo secrets
gh secret set AWS_ACCESS_KEY_ID --body "$AWS_ACCESS_KEY_ID"
echo "✅ GitHub AWS_ACCESS_KEY_ID updated."

gh secret set AWS_SECRET_ACCESS_KEY --body "$AWS_SECRET_ACCESS_KEY"
echo "✅ GitHub AWS_SECRET_ACCESS_KEY updated."

if [ -n "$AWS_SESSION_TOKEN" ]; then
  gh secret set AWS_SESSION_TOKEN --body "$AWS_SESSION_TOKEN"
  echo "✅ GitHub AWS_SESSION_TOKEN updated."
else
  # If empty, delete or set empty so it doesn't break non-lab auth
  gh secret remove AWS_SESSION_TOKEN >/dev/null 2>&1 || true
  echo "✅ GitHub AWS_SESSION_TOKEN cleared (removed)."
fi

echo "Success! Your GitHub Actions pipeline now has the latest ephemeral lab credentials."
