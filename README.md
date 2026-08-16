# AI CV SaaS

AI-powered CV/Resume SaaS built as a production-oriented AWS application.

The platform transforms an existing customer CV into a professionally rewritten, ATS-friendly CV while reducing a manual 2-4 hour workflow to approximately 10-20 minutes of human review.

> Status: Architecture and MVP foundation in progress.

---

## Business Problem

The original CV service requires significant manual work: understanding the customer's background and target role, rewriting the content, transferring it into a template, formatting it, handling revisions, collecting payment, and delivering the final files.

The service has demonstrated real customer demand, but the manual workflow does not scale.

The goal of this project is to automate the repeatable work while retaining human quality control during the MVP phase.

---

## Product Goal

Reduce a professional CV order from approximately **2-4 hours of manual work** to approximately **10-20 minutes of human review**.

The long-term goal is to make standard CV orders largely self-service while retaining a premium human-reviewed service.

---

## MVP Customer Flow

Upload Existing CV
→ Enter Target Role
→ Optional Job Description
→ Extract Existing CV Information
→ AI Rewrite / Optimization
→ Canonical Structured CV Data
→ Select ATS-Friendly Template
→ Generate Preview
→ Customer / Human Review
→ Payment
→ Generate Final PDF + DOCX
→ Customer Delivery

---

## Architecture Principles

- AI generates and improves structured CV content.
- AI does not design the final PDF.
- PDF and DOCX output uses deterministic templates.
- Prefer serverless AWS services where they reduce operational overhead.
- Manage infrastructure using Terraform.
- Implement CI/CD using GitHub Actions.
- Require automated testing before production deployment.
- Separate development and production environments.
- Keep customer CV files private.
- Never commit secrets to Git.
- Do not write personally identifiable CV content to application logs.
- Keep infrastructure inexpensive at low traffic.
- Avoid premature microservices and unnecessary AWS services.

---

## Planned AWS Architecture

Customer Browser
→ S3 + CloudFront
→ React / TypeScript
→ API Gateway
→ Python Lambda
→ DynamoDB / S3
→ SQS
→ Processing Worker
→ Document Parser + AI Provider
→ Structured CV JSON
→ Deterministic Renderer
→ PDF + DOCX

Additional platform services:

- Amazon Cognito — authentication
- Amazon CloudWatch — logs, metrics and alarms
- AWS Secrets Manager / SSM Parameter Store — secrets
- Amazon SQS DLQ — failed background jobs
- Stripe — payments
- GitHub Actions — CI/CD
- Terraform — Infrastructure as Code

---

## Technology Stack

### Backend

- Python
- Pydantic
- AWS Lambda
- API Gateway
- DynamoDB
- S3
- SQS

### Frontend

- React
- TypeScript
- Vite

### Infrastructure / DevOps

- Terraform
- Git
- GitHub
- GitHub Actions
- AWS IAM
- CloudWatch
- Ruff
- mypy
- pytest

### AI / Document Processing

- OpenAI API initially
- Structured AI outputs
- PDF text extraction
- DOCX extraction
- Deterministic PDF/DOCX generation

---

## Security and Privacy

CVs may contain personally identifiable information such as names, contact information, employment history, education and addresses.

Security requirements include:

- Private S3 buckets
- S3 Block Public Access
- HTTPS-only access
- Short-lived presigned URLs
- Encryption at rest
- Least-privilege IAM
- Secret management outside Git
- Restricted application logging
- Automatic document retention/deletion policies

---

## Environments

Local Development
→ AWS Development
→ AWS Production

Development and production infrastructure will be isolated using Terraform environment configuration.

---

## Engineering Decisions

Important technical decisions are documented as Architecture Decision Records under `docs/adr/`.

Examples include:

- Serverless vs server/container architecture
- DynamoDB vs relational database
- SQS asynchronous processing
- Canonical CV schema
- AI provider abstraction
- Deterministic document rendering
- Development vs production isolation
- Customer file retention strategy

---

## MVP Non-Goals

The first release intentionally excludes:

- AI agents
- Interview preparation
- Job application automation
- LinkedIn optimization
- Cover letters
- Subscriptions
- Recruiter portals
- Mobile applications
- Dozens of CV templates
- Canva-style visual editing
- Kubernetes / EKS
- Redis
- Unnecessary microservices
- Advanced ATS scoring systems

These features may be evaluated after the core CV workflow has real production users.

---

## DevOps / Cloud Learning Objectives

This project demonstrates practical experience with:

- AWS serverless architecture
- Infrastructure as Code
- CI/CD
- IAM and least privilege
- Asynchronous/event-driven processing
- API design
- Object storage
- NoSQL data modeling
- Secrets management
- Observability
- Automated testing
- Environment isolation
- Cost optimization
- Secure handling of customer data
- External AI and payment API integration

---

## Current Development Stage

### Completed

- [x] MVP scope defined
- [x] Architecture baseline defined
- [x] Repository structure created
- [x] Development tooling baseline created

### In Progress

- [ ] Canonical structured CV data model

### Upcoming

- [ ] Backend foundation
- [ ] Local CV parsing
- [ ] AI structured-output pipeline
- [ ] AWS development infrastructure
- [ ] CV template engine
- [ ] Admin review workflow
- [ ] Payments
- [ ] CI/CD
- [ ] Production hardening
- [ ] Beta launch

---

## Project Philosophy

Build the smallest production-quality system capable of serving real paying customers.

Do not add infrastructure or features simply for technical complexity.

Every major component must have a clear product, reliability, security, scalability, or operational reason to exist.
