# ADR-0004: Separate Order State from CV Document Storage

## Status

Accepted

## Context

The AI CV SaaS must persist several different categories of data:

- customer order state
- processing status
- payment status
- template selection
- uploaded source documents
- canonical structured CV data
- revised CV versions
- generated previews
- final PDF documents
- final DOCX documents
- timestamps and object references

These data types have different access patterns and lifecycle requirements.

The canonical CV is structured JSON, but it behaves more like a versioned document than a frequently queried database record.

## Decision

Use DynamoDB for transactional application state and metadata.

Use Amazon S3 for source documents, structured CV JSON documents, previews, and generated deliverables.

## DynamoDB Responsibilities

DynamoDB will store order-oriented metadata such as:

- order_id
- customer_id
- order_status
- processing_status
- target_job_title
- target_industry
- selected_template
- payment_status
- AI provider
- AI model
- current CV version
- S3 object references
- created_at
- updated_at

The table will be designed around application access patterns rather than relational normalization.

## S3 Responsibilities

S3 will store:

- original customer upload
- canonical CV JSON versions
- generated preview documents
- final PDF
- final DOCX

Customer document objects must remain private.

## Canonical CV Storage

The full CanonicalCV will not be treated as the primary DynamoDB document payload.

Each saved CV version will be serialized as JSON and stored in S3.

DynamoDB will reference the current canonical CV object using metadata such as:

- current_cv_s3_key
- current_cv_version

This separates application workflow state from versioned document content.

## Versioning

CV revisions must not silently overwrite prior versions during the human-review workflow.

A possible object structure is:

orders/{order_id}/source/original.docx

orders/{order_id}/cv/v1.json
orders/{order_id}/cv/v2.json
orders/{order_id}/cv/v3.json

orders/{order_id}/preview/v3.pdf

orders/{order_id}/final/cv.pdf
orders/{order_id}/final/cv.docx

The exact naming convention may evolve during implementation.

## Benefits

### DynamoDB

- fast order/status lookups
- serverless scaling
- low idle cost
- simple workflow-state updates
- suitable for asynchronous processing state

### S3

- inexpensive document storage
- natural support for source and generated files
- lifecycle expiration policies
- version-oriented object organization
- avoids large document payloads in DynamoDB
- simple future integration with presigned URLs

## Alternatives Considered

### Store Full CanonicalCV in DynamoDB

Rejected as the primary persistence strategy.

Although technically possible, it would mix workflow metadata and versioned document content in one storage layer.

It would also make document-version history and lifecycle management less natural.

### Store Everything in S3

Rejected because querying order status, payment state, processing failures, and admin queues would become inefficient.

### Use RDS

Rejected for the MVP because current access patterns do not justify relational database operational complexity or continuous database cost.

RDS may be reconsidered if future requirements introduce complex relational reporting, joins, or transactional workflows.

## Privacy and Retention

All customer document objects must remain private.

Access must use application authorization and short-lived mechanisms such as presigned URLs where appropriate.

Source and generated document objects will have explicit retention policies.

Initial proposed policy:

- source CV: delete after 30 days following completed delivery
- generated preview: delete after 30 days
- final generated documents: delete after 30 days unless business requirements justify longer retention
- business/order metadata: retained separately according to operational/accounting requirements

Retention values may change before production launch.

## Consequences

### Benefits

- clear separation of concerns
- easier CV versioning
- simple document retention
- efficient order queries
- low-cost serverless architecture
- avoids database coupling to document rendering

### Trade-offs

- application must coordinate DynamoDB metadata with S3 objects
- orphaned objects must be considered during failure handling
- version updates require careful ordering
- deletion workflows must handle both DynamoDB and S3

## Future Review

Revisit this decision if:

- CV documents require complex querying
- collaborative editing becomes a major feature
- transactional requirements exceed simple order-state updates
- document retention requirements materially change
- relational reporting becomes important
