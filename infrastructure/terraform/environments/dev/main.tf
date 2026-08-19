data "aws_caller_identity" "current" {}

locals {
  name_prefix = "${var.project_name}-${var.environment}"

  document_bucket_name = lower(
    "${local.name_prefix}-documents-${data.aws_caller_identity.current.account_id}"
  )
}

resource "aws_s3_bucket" "documents" {
  bucket = local.document_bucket_name
}

resource "aws_s3_bucket_public_access_block" "documents" {
  bucket = aws_s3_bucket.documents.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "documents" {
  bucket = aws_s3_bucket.documents.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_dynamodb_table" "orders" {
  name         = "${local.name_prefix}-orders"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "order_id"

  attribute {
    name = "order_id"
    type = "S"
  }

  attribute {
    name = "customer_id"
    type = "S"
  }

  attribute {
    name = "order_status"
    type = "S"
  }

  attribute {
    name = "processing_status"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "S"
  }

  global_secondary_index {
    name            = "customer-created-at-index"
    hash_key        = "customer_id"
    range_key       = "created_at"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "order-status-created-at-index"
    hash_key        = "order_status"
    range_key       = "created_at"
    projection_type = "ALL"
  }

  global_secondary_index {
    name            = "processing-status-created-at-index"
    hash_key        = "processing_status"
    range_key       = "created_at"
    projection_type = "ALL"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "documents" {
  bucket = aws_s3_bucket.documents.id

  depends_on = [
    aws_s3_bucket_versioning.documents
  ]

  rule {
    id     = "expire-customer-documents"
    status = "Enabled"

    filter {}

    expiration {
      days = 30
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

data "aws_iam_policy_document" "documents_https_only" {
  statement {
    sid    = "DenyInsecureTransport"
    effect = "Deny"

    actions = [
      "s3:*"
    ]

    resources = [
      aws_s3_bucket.documents.arn,
      "${aws_s3_bucket.documents.arn}/*"
    ]

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "documents_https_only" {
  bucket = aws_s3_bucket.documents.id
  policy = data.aws_iam_policy_document.documents_https_only.json

  depends_on = [
    aws_s3_bucket_public_access_block.documents
  ]
}
