output "aws_region" {
  description = "AWS region used by the DEV environment."
  value       = var.aws_region
}

output "documents_bucket_name" {
  description = "Private S3 bucket used for CV documents."
  value       = aws_s3_bucket.documents.bucket
}

output "orders_table_name" {
  description = "DynamoDB table used for CV orders."
  value       = aws_dynamodb_table.orders.name
}

output "orders_table_arn" {
  description = "ARN of the DynamoDB orders table."
  value       = aws_dynamodb_table.orders.arn
}
