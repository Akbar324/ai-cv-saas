# ADR-0002: Use a Canonical Structured CV Data Model

## Status

Accepted

## Context

The AI CV SaaS receives customer CVs in different formats and layouts.

The system must support:

- PDF and DOCX extraction
- AI rewriting and optimization
- structured validation
- admin editing
- customer preview
- template switching
- PDF generation
- DOCX generation
- future API integrations

Allowing each component to use its own representation would create duplication and inconsistent behavior.

## Decision

Use one canonical structured CV data model as the internal source of truth.

The initial top-level structure will contain:

- personal_details
- target_role
- professional_summary
- skills
- work_experience
- education
- certifications
- languages
- projects
- additional_information

The model will be implemented using Python Pydantic models.

All AI-generated CV content must validate against this schema before being persisted or rendered.

## Design Principles

### Structured Over Free-Form

CV sections are represented using typed fields and lists rather than one large block of text.

### Facts and Presentation Are Separate

The canonical model stores CV content and factual information.

Template styling, fonts, spacing, colors and visual layout are not stored in the CV data model.

### Optional Sections

Sections such as certifications, languages and projects may be absent for some candidates.

The renderer must handle missing optional sections gracefully.

### No Fabricated Information

AI may improve wording and organization but must not invent:

- employers
- job titles
- employment dates
- degrees
- certifications
- numerical achievements
- skills not supported by customer information

### Template Independence

All supported templates consume the same canonical CV model.

Changing templates must not require another AI generation request.

## Initial Data Model

### Personal Details

- full_name
- professional_title
- email
- phone
- location
- linkedin_url
- portfolio_url

### Target Role

- job_title
- industry
- job_description

### Professional Summary

A concise optimized summary stored as text.

### Skills

A list of relevant skills.

### Work Experience

Each work experience entry contains:

- company
- job_title
- location
- start_date
- end_date
- is_current
- responsibilities_or_achievements

Responsibilities and achievements are stored as a list of bullet strings.

### Education

Each education entry contains:

- institution
- qualification
- field_of_study
- location
- start_date
- end_date

### Certifications

Each certification entry contains:

- name
- issuer
- issue_date
- expiry_date
- credential_id
- credential_url

### Languages

Each language entry contains:

- language
- proficiency

### Projects

Each project entry contains:

- name
- description
- technologies
- url

### Additional Information

Optional additional sections that do not fit the standard model.

## Alternatives Considered

### Store Raw AI Markdown

Rejected because parsing and deterministic rendering would be unreliable.

### Store Final HTML

Rejected because presentation would become tightly coupled to content and template switching would become difficult.

### Store DOCX as the Source of Truth

Rejected because editing, AI optimization and multi-template rendering would be difficult.

### Allow Different Schemas Per Template

Rejected because templates should be presentation layers, not data models.

## Consequences

### Benefits

- predictable AI output
- strong validation
- deterministic rendering
- easier testing
- simpler admin editing
- template independence
- easier future integrations

### Trade-offs

- schema changes must be managed carefully
- unusual CV structures may require mapping into standard sections
- migration may be required if the schema changes significantly later

## Future Review

Revisit the schema when real customer CVs reveal repeated information that cannot be represented cleanly by the current model.
