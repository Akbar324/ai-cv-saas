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

# ---------------------------------------------------------------------------
# Backend API Lambda
# ---------------------------------------------------------------------------

locals {
  api_lambda_name     = "${local.name_prefix}-api"
  api_lambda_zip_path = "${path.root}/../../../../build/lambda/api.zip"
}

resource "aws_cloudwatch_log_group" "api_lambda" {
  name              = "/aws/lambda/${local.api_lambda_name}"
  retention_in_days = 14
}

data "aws_iam_policy_document" "api_lambda_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type = "Service"

      identifiers = [
        "lambda.amazonaws.com"
      ]
    }

    actions = [
      "sts:AssumeRole"
    ]
  }
}

resource "aws_iam_role" "api_lambda" {
  name               = "${local.api_lambda_name}-role"
  assume_role_policy = data.aws_iam_policy_document.api_lambda_assume_role.json
}

data "aws_iam_policy_document" "api_lambda_permissions" {
  statement {
    sid    = "WriteCloudWatchLogs"
    effect = "Allow"

    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]

    resources = [
      "${aws_cloudwatch_log_group.api_lambda.arn}:*"
    ]
  }

  statement {
    sid    = "ReadWriteOrders"
    effect = "Allow"

    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem"
    ]

    resources = [
      aws_dynamodb_table.orders.arn
    ]
  }

  statement {
    sid    = "UploadSourceCV"
    effect = "Allow"

    actions = [
      "s3:PutObject"
    ]

    resources = [
      "${aws_s3_bucket.documents.arn}/orders/*/source/*"
    ]
  }
}

resource "aws_iam_role_policy" "api_lambda" {
  name   = "${local.api_lambda_name}-permissions"
  role   = aws_iam_role.api_lambda.id
  policy = data.aws_iam_policy_document.api_lambda_permissions.json
}

resource "aws_lambda_function" "api" {
  function_name = local.api_lambda_name
  role          = aws_iam_role.api_lambda.arn

  runtime = "python3.12"
  handler = "backend.app.lambda_handler.lambda_handler"

  filename         = local.api_lambda_zip_path
  source_code_hash = filebase64sha256(local.api_lambda_zip_path)

  architectures = [
    "x86_64"
  ]

  memory_size = 512
  timeout     = 20

  environment {
    variables = {
      APP_ENV               = "development"
      DOCUMENTS_BUCKET_NAME = aws_s3_bucket.documents.bucket
      ORDERS_TABLE_NAME     = aws_dynamodb_table.orders.name
      PROCESSING_QUEUE_URL  = aws_sqs_queue.processing.url
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.api_lambda,
    aws_iam_role_policy.api_lambda
  ]
}

# ---------------------------------------------------------------------------
# API Gateway HTTP API
# ---------------------------------------------------------------------------

resource "aws_apigatewayv2_api" "api" {
  name          = "${local.name_prefix}-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_headers = [
      "content-type",
      "authorization"
    ]

    allow_methods = [
      "GET",
      "POST",
      "OPTIONS"
    ]

    allow_origins = [
      "http://localhost:3000",
      "http://localhost:5173"
    ]

    max_age = 300
  }
}

resource "aws_apigatewayv2_integration" "api_lambda" {
  api_id = aws_apigatewayv2_api.api.id

  integration_type   = "AWS_PROXY"
  integration_uri    = aws_lambda_function.api.invoke_arn
  integration_method = "POST"

  payload_format_version = "2.0"
  timeout_milliseconds   = 20000
}

resource "aws_apigatewayv2_route" "create_order" {
  api_id = aws_apigatewayv2_api.api.id

  route_key = "POST /orders"
  target    = "integrations/${aws_apigatewayv2_integration.api_lambda.id}"
}

resource "aws_apigatewayv2_route" "get_order" {
  api_id = aws_apigatewayv2_api.api.id

  route_key = "GET /orders/{order_id}"
  target    = "integrations/${aws_apigatewayv2_integration.api_lambda.id}"
}

resource "aws_apigatewayv2_route" "create_upload_target" {
  api_id = aws_apigatewayv2_api.api.id

  route_key = "POST /orders/{order_id}/upload-url"
  target    = "integrations/${aws_apigatewayv2_integration.api_lambda.id}"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id = aws_apigatewayv2_api.api.id

  name        = "$default"
  auto_deploy = true

  default_route_settings {
    detailed_metrics_enabled = false
    throttling_burst_limit   = 20
    throttling_rate_limit    = 10
  }
}

resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.api.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_apigatewayv2_api.api.execution_arn}/*/*"
}

# ---------------------------------------------------------------------------
# Asynchronous CV processing queue
# ---------------------------------------------------------------------------

resource "aws_sqs_queue" "processing_dlq" {
  name                      = "${local.name_prefix}-processing-dlq"
  message_retention_seconds = 1209600
}

resource "aws_sqs_queue" "processing" {
  name = "${local.name_prefix}-processing"

  visibility_timeout_seconds = 900
  message_retention_seconds  = 345600

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.processing_dlq.arn
    maxReceiveCount     = 3
  })
}

data "aws_secretsmanager_secret" "gemini_api_key" {
  name = "ai-cv-saas/dev/gemini-api-key"
}

# ---------------------------------------------------------------------------
# API permission to enqueue processing jobs
# ---------------------------------------------------------------------------

data "aws_iam_policy_document" "api_lambda_async_permissions" {
  statement {
    sid    = "QueueCVProcessing"
    effect = "Allow"

    actions = [
      "sqs:SendMessage"
    ]

    resources = [
      aws_sqs_queue.processing.arn
    ]
  }
}

resource "aws_iam_role_policy" "api_lambda_async" {
  name   = "${local.api_lambda_name}-async-processing"
  role   = aws_iam_role.api_lambda.id
  policy = data.aws_iam_policy_document.api_lambda_async_permissions.json
}

# ---------------------------------------------------------------------------
# Worker Lambda
# ---------------------------------------------------------------------------

locals {
  worker_lambda_name = "${local.name_prefix}-worker"
  worker_zip_path    = "${path.root}/../../../../build/lambda/worker.zip"
}

resource "aws_cloudwatch_log_group" "worker_lambda" {
  name              = "/aws/lambda/${local.worker_lambda_name}"
  retention_in_days = 14
}

data "aws_iam_policy_document" "worker_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = [
      "sts:AssumeRole"
    ]
  }
}

resource "aws_iam_role" "worker" {
  name               = "${local.worker_lambda_name}-role"
  assume_role_policy = data.aws_iam_policy_document.worker_assume_role.json
}

data "aws_iam_policy_document" "worker_permissions" {
  statement {
    sid    = "WorkerLogs"
    effect = "Allow"

    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]

    resources = [
      "${aws_cloudwatch_log_group.worker_lambda.arn}:*"
    ]
  }

  statement {
    sid    = "Orders"
    effect = "Allow"

    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem"
    ]

    resources = [
      aws_dynamodb_table.orders.arn
    ]
  }

  statement {
    sid    = "Documents"
    effect = "Allow"

    actions = [
      "s3:GetObject",
      "s3:PutObject"
    ]

    resources = [
      "${aws_s3_bucket.documents.arn}/orders/*"
    ]
  }

  statement {
    sid    = "GeminiSecret"
    effect = "Allow"

    actions = [
      "secretsmanager:GetSecretValue"
    ]

    resources = [
      data.aws_secretsmanager_secret.gemini_api_key.arn
    ]
  }

  statement {
    sid    = "ConsumeProcessingQueue"
    effect = "Allow"

    actions = [
      "sqs:ReceiveMessage",
      "sqs:DeleteMessage",
      "sqs:GetQueueAttributes"
    ]

    resources = [
      aws_sqs_queue.processing.arn
    ]
  }
}

resource "aws_iam_role_policy" "worker" {
  name   = "${local.worker_lambda_name}-permissions"
  role   = aws_iam_role.worker.id
  policy = data.aws_iam_policy_document.worker_permissions.json
}

resource "aws_lambda_function" "worker" {
  function_name = local.worker_lambda_name
  role          = aws_iam_role.worker.arn

  runtime = "python3.12"
  handler = "backend.app.worker_handler.lambda_handler"

  filename         = local.worker_zip_path
  source_code_hash = filebase64sha256(local.worker_zip_path)

  architectures = ["x86_64"]

  memory_size = 1024
  timeout     = 120

  environment {
    variables = {
      APP_ENV               = "development"
      DOCUMENTS_BUCKET_NAME = aws_s3_bucket.documents.bucket
      ORDERS_TABLE_NAME     = aws_dynamodb_table.orders.name

      AI_PROVIDER  = "gemini"
      AI_MODEL     = "gemini-3.1-flash-lite"
      AI_SECRET_ID = data.aws_secretsmanager_secret.gemini_api_key.arn
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.worker_lambda,
    aws_iam_role_policy.worker
  ]
}

resource "aws_lambda_event_source_mapping" "processing" {
  event_source_arn = aws_sqs_queue.processing.arn
  function_name    = aws_lambda_function.worker.arn

  batch_size = 1

  function_response_types = [
    "ReportBatchItemFailures"
  ]
}

# ---------------------------------------------------------------------------
# API processing route
# ---------------------------------------------------------------------------

resource "aws_apigatewayv2_route" "process_order" {
  api_id = aws_apigatewayv2_api.api.id

  route_key = "POST /orders/{order_id}/process"
  target    = "integrations/${aws_apigatewayv2_integration.api_lambda.id}"
}

# ---------------------------------------------------------------------------
# Async processing observability
# ---------------------------------------------------------------------------

resource "aws_cloudwatch_metric_alarm" "worker_errors" {
  alarm_name          = "${local.worker_lambda_name}-errors"
  alarm_description   = "Worker Lambda reported one or more errors."
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  threshold           = 1

  namespace   = "AWS/Lambda"
  metric_name = "Errors"
  statistic   = "Sum"
  period      = 300

  treat_missing_data = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.worker.function_name
  }
}

resource "aws_cloudwatch_metric_alarm" "processing_dlq_messages" {
  alarm_name          = "${local.name_prefix}-processing-dlq-messages"
  alarm_description   = "Messages are visible in the CV processing DLQ."
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  threshold           = 1

  namespace   = "AWS/SQS"
  metric_name = "ApproximateNumberOfMessagesVisible"
  statistic   = "Maximum"
  period      = 300

  treat_missing_data = "notBreaching"

  dimensions = {
    QueueName = aws_sqs_queue.processing_dlq.name
  }
}
