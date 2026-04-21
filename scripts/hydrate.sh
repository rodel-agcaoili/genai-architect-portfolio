#!/bin/bash
# scripts/hydrate.sh

echo "Enter AWS_ACCESS_KEY_ID (Starts with AKIA):"
read -r access_key
echo "Enter AWS_SECRET_ACCESS_KEY:"
read -s secret_key
echo ""
echo "Enter AWS_SESSION_TOKEN (Leave BLANK if you have an AKIA key):"
read -s session_token
echo ""

# Update Mandatory Secrets
gh secret set AWS_ACCESS_KEY_ID -b"$access_key"
gh secret set AWS_SECRET_ACCESS_KEY -b"$secret_key"
gh secret set AWS_REGION -b"us-east-1"

# Handle Optional Token
if [ -z "$session_token" ]; then
    echo "No token provided. Removing old session token from GitHub..."
    gh secret delete AWS_SESSION_TOKEN 2>/dev/null || true
else
    echo "Token provided. Updating GitHub..."
    gh secret set AWS_SESSION_TOKEN -b"$session_token"
fi

echo "GitHub Secrets updated! Check your Actions tab."