resource "aws_opensearchserverless_collection" "vector_store" {
  name        = "rag-collection"
  type        = "VECTORSEARCH"
  description = "Vector store for the Secure RAG project"
}

resource "aws_opensearchserverless_access_policy" "data_access" {
  name        = "rag-access-policy"
  type        = "data"
  description = "Allow Lambda to read/write to the collection"
  policy = jsonencode([
    {
      Rules = [
        {
          ResourceType = "collection"
          Resource     = ["collection/${aws_opensearchserverless_collection.vector_store.name}"]
          Permission   = ["aoss:CreateCollectionItems", "aoss:DeleteCollectionItems", "aoss:UpdateCollectionItems", "aoss:DescribeCollectionItems"]
        },
        {
          ResourceType = "index"
          Resource     = ["index/${aws_opensearchserverless_collection.vector_store.name}/*"]
          Permission   = ["aoss:CreateIndex", "aoss:DeleteIndex", "aoss:UpdateIndex", "aoss:DescribeIndex", "aoss:ReadDocument", "aoss:WriteDocument"]
        }
      ]
      Principal = [aws_iam_role.rag_lambda_role.arn]
    }
  ])
}
