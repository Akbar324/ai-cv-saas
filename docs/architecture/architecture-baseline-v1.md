# Architecture Baseline V1

## Product

AI-powered CV/Resume SaaS using an AI + human approval workflow.

## Core MVP

1. Existing CV upload: PDF/DOCX
2. CV information extraction
3. Target role input
4. Optional job description
5. AI rewriting and optimization
6. Structured canonical CV data
7. ATS-friendly templates
8. CV preview
9. Human approval/revision
10. Payment
11. Final PDF/DOCX generation
12. Customer delivery
13. Simple admin/order management

## Initial Architecture

### Frontend

- React
- TypeScript
- Vite
- S3 + CloudFront

### Authentication

- Amazon Cognito

### API

- Amazon API Gateway HTTP API
- Python Lambda

### Database

- DynamoDB On-Demand

### Files

- Private Amazon S3

### Background Processing

- Amazon SQS
- Dead-letter queue
- Lambda worker

### AI

- AI provider abstraction
- OpenAI initially
- Structured output validated before persistence

### Document Rendering

- Deterministic templates
- PDF generation
- DOCX generation

### Payments

- Stripe Checkout
- Stripe webhook

### Monitoring

- Amazon CloudWatch

### Secrets

- AWS Secrets Manager and/or SSM Parameter Store

### Infrastructure

- Terraform

### CI/CD

- GitHub Actions

### Environments

- Local
- Development
- Production

## Explicit Non-Goals for V1

- Cover letters
- LinkedIn optimization
- Interview preparation
- AI agents
- Job search/application automation
- Dozens of templates
- Subscriptions
- Mobile applications
- Recruiter/employer portals
- Canva-style visual editor
- Kubernetes/EKS
- Redis
- RDS unless later requirements justify it
- Microservices
- Advanced ATS scoring platform
