# ADR-0001: Use a Serverless Architecture for the MVP

## Status

Accepted

## Context

The AI CV SaaS is expected to have low and unpredictable traffic during its MVP phase.

The application needs:

- HTTP APIs
- document storage
- background CV processing
- AI API integration
- order persistence
- authentication
- monitoring
- low operating cost

The product will initially be developed part-time and should minimize infrastructure operations.

## Decision

Use a primarily serverless AWS architecture consisting of:

- API Gateway
- AWS Lambda
- DynamoDB On-Demand
- Amazon S3
- Amazon SQS
- Amazon Cognito
- Amazon CloudWatch

Terraform will manage infrastructure.

## Alternatives Considered

### EC2

Rejected for the MVP because it would require server provisioning, patching, scaling and continuous runtime cost.

### ECS / Fargate

A valid future option for workloads that exceed Lambda limits or require long-running containers.

Not required for the initial workload.

### EKS / Kubernetes

Rejected for the MVP.

Kubernetes would add significant operational complexity without solving a current product requirement.

### Relational Database

A relational database may become appropriate if future requirements require complex joins, reporting or transactional relationships.

For the initial order-oriented access patterns, DynamoDB provides a simpler serverless option.

## Consequences

### Benefits

- Low idle cost
- Minimal infrastructure administration
- Automatic scaling
- Strong AWS learning value
- Event-driven architecture experience
- Easy integration with managed AWS services

### Trade-offs

- Lambda execution limits
- DynamoDB requires careful access-pattern design
- Local development differs from the AWS runtime
- Serverless observability requires deliberate correlation and logging design

## Future Review

Revisit this decision if:

- document generation exceeds Lambda runtime/resource constraints
- traffic patterns change significantly
- background workloads become long-running
- relational query requirements become important
