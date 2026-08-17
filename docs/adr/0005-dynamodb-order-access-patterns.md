# ADR-0005: Design DynamoDB Around Order Access Patterns

## Status

Accepted

## Context

The AI CV SaaS needs persistent order metadata for customer workflows, admin review, background processing, and payment state.

The MVP requires predictable low-volume queries rather than relational reporting.

DynamoDB table and index design must therefore be derived from known access patterns.

## Required MVP Access Patterns

The application must support:

1. Get one order by order_id.
2. List orders for one customer, newest first.
3. List orders by order_status, newest first.
4. List orders by processing_status, newest first.
5. List recent orders for the admin dashboard.

## Decision

Use one DynamoDB orders table.

### Primary Key

Partition key:

- order_id

No sort key is required for the primary table because each order is represented by one current metadata record.

## Global Secondary Indexes

### Customer Orders Index

Purpose:

List one customer's orders newest first.

Keys:

- partition key: customer_id
- sort key: created_at

Example query:

customer_id = customer-001

Results are sorted by created_at.

### Order Status Index

Purpose:

Support business workflow queues such as:

- human_review
- revision_required
- approved
- delivered

Keys:

- partition key: order_status
- sort key: created_at

Example query:

order_status = human_review

This becomes the primary admin human-review queue.

### Processing Status Index

Purpose:

Support technical processing queues and operational troubleshooting.

Relevant values include:

- pending
- processing
- succeeded
- failed

Keys:

- partition key: processing_status
- sort key: created_at

Example query:

processing_status = failed

This supports operational visibility and retry workflows.

## Admin Recent Orders

The MVP does not initially require a dedicated index for all recent orders.

Because order volume is expected to be low during validation, the admin dashboard may use a controlled paginated Scan for the recent-order view.

This is accepted only for the MVP.

A dedicated admin index should be introduced if production volume makes Scan inefficient or expensive.

## Timestamps

created_at and updated_at will be stored as UTC ISO-8601 strings.

Example:

2026-08-18T12:30:00+00:00

Using sortable ISO-8601 timestamps allows chronological ordering in DynamoDB sort keys.

## Pagination

All list operations must support pagination.

Application APIs must not assume that DynamoDB returns all matching records in a single response.

Repository methods will expose continuation information based on DynamoDB LastEvaluatedKey.

## Consistency

Get-by-ID may use eventually consistent reads by default unless a workflow explicitly requires strong consistency.

GSI queries are eventually consistent because DynamoDB global secondary indexes do not support strongly consistent reads.

The MVP workflow must therefore tolerate short propagation delays between table updates and index visibility.

## Index Projection

Initial GSIs should project the attributes required by list/admin views.

Avoid projecting unnecessary large metadata.

The final projection choice will be made during Terraform implementation after repository response models are defined.

## Attributes Stored in the Order Record

The order record may contain:

- order_id
- customer_id
- order_status
- processing_status
- payment_status
- target_job_title
- target_industry
- selected_template
- ai_provider
- ai_model
- current_cv_version
- source_s3_key
- current_cv_s3_key
- preview_s3_key
- final_pdf_s3_key
- final_docx_s3_key
- created_at
- updated_at

The application domain model may group document references internally even if persistence serialization uses flat attributes.

## Alternatives Considered

### Customer ID as the Primary Partition Key

Rejected because orders are primarily addressed using unique order IDs and each order is one current metadata record.

It would require a composite key for direct order retrieval and complicate common application operations.

### Single-Table Design for Multiple Entity Types

Not selected for the MVP.

A broader DynamoDB single-table architecture could combine customers, orders, revisions, payments, and other entities.

The current product does not yet have enough stable access patterns to justify that additional modeling complexity.

### One Index for Every Possible Admin Filter

Rejected because additional indexes increase cost and maintenance complexity.

Only known MVP access patterns justify indexes.

### RDS

Rejected for the MVP because current data relationships and query requirements do not justify relational database infrastructure.

## Consequences

### Benefits

- simple primary lookup
- efficient customer order history
- efficient human-review queue
- efficient failed-processing visibility
- low operational overhead
- clear access-pattern-driven design

### Trade-offs

- additional GSIs consume storage and write capacity
- GSI reads are eventually consistent
- admin recent-order Scan is intentionally temporary
- new query patterns may require additional indexes later

## Future Review

Revisit this design if:

- admin order volume makes Scan inefficient
- additional workflow queues require new query dimensions
- customer or payment entities require richer access patterns
- analytics/reporting needs increase
- the product requires a broader DynamoDB single-table design
