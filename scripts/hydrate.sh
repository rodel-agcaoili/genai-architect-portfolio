#!/bin/bash
# scripts/hydrate.sh

echo "Enter AWS_ACCESS_KEY_ID:"
read -r access_key
echo "Enter AWS_SECRET_ACCESS_KEY:"
read -s secret_key
echo ""
echo "Enter AWS_SESSION_TOKEN:"
read -s session_token
echo ""

# Update GitHub Secrets
gh secret set AWS_ACCESS_KEY_ID -b"$access_key"
gh secret set AWS_SECRET_ACCESS_KEY -b"$secret_key"
gh secret set AWS_SESSION_TOKEN -b"$session_token"
gh secret set AWS_REGION -b"us-east-1"

echo "GitHub Secrets updated. Pipeline should trigger automatically."