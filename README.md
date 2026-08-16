# AI CV SaaS

Production AWS SaaS for AI-assisted CV/resume optimization and deterministic document generation.

## Product Goal

Reduce a professional CV order from approximately 2-4 hours of manual work to approximately 10-20 minutes of human review.

## MVP Flow

Upload existing CV
→ Extract structured information
→ Optimize content for target role/job description
→ Store canonical CV data
→ Select ATS-friendly template
→ Generate preview
→ Human review/revision
→ Payment
→ Generate final PDF/DOCX
→ Customer delivery

## Architecture Principles

- AI generates structured CV content, not final document design.
- Deterministic templates generate PDF/DOCX output.
- Serverless AWS architecture where appropriate.
- Infrastructure as Code using Terraform.
- Automated testing and CI/CD.
- Development and production environments are separated.
- Customer CV data is private and has a defined retention policy.
- Secrets must never be committed to Git.
- Avoid unnecessary infrastructure and premature microservices.
