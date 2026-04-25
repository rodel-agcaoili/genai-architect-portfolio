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

# Use GitHub CLI to securely set repo secrets
gh secret set AWS_ACCESS_KEY_ID --body "$AWS_ACCESS_KEY_ID"
echo "✅ AWS_ACCESS_KEY_ID updated."

gh secret set AWS_SECRET_ACCESS_KEY --body "$AWS_SECRET_ACCESS_KEY"
echo "✅ AWS_SECRET_ACCESS_KEY updated."

if [ -n "$AWS_SESSION_TOKEN" ]; then
  gh secret set AWS_SESSION_TOKEN --body "$AWS_SESSION_TOKEN"
  echo "✅ AWS_SESSION_TOKEN updated."
else
  # If empty, delete or set empty so it doesn't break non-lab auth
  gh secret set AWS_SESSION_TOKEN --body ""
  echo "✅ AWS_SESSION_TOKEN cleared (not provided)."
fi

echo "Success! Your GitHub Actions pipeline now has the latest ephemeral lab credentials."
