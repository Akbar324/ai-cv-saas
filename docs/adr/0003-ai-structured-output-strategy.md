# ADR-0003: Use Structured AI Output Behind a Provider Abstraction

## Status

Accepted

## Context

The AI CV SaaS must transform extracted customer CV text into the canonical CV data model.

AI output will eventually be used by:

- admin review
- customer preview
- CV templates
- PDF rendering
- DOCX rendering
- persistent order data

Allowing free-form AI responses would make downstream parsing unreliable.

Directly coupling application services to one AI provider would also make testing, provider changes, and future cost optimization more difficult.

Customer CVs may contain personally identifiable information, so unnecessary provider-side retention should be avoided.

## Decision

Introduce an internal AI service boundary that accepts normalized document text and targeting information and returns a validated CanonicalCV.

The initial provider will be OpenAI.

The OpenAI implementation will use:

- the Responses API
- Structured Outputs
- a JSON Schema derived from the canonical Pydantic model
- provider-side response storage disabled for customer CV processing

The rest of the application must depend on the internal AI service contract rather than directly depending on OpenAI SDK objects.

## Processing Flow

ExtractedDocument
→ AI service request
→ provider implementation
→ structured model response
→ CanonicalCV validation
→ downstream persistence/review/rendering

## AI Responsibilities

The AI may:

- reorganize CV information
- improve wording
- improve clarity
- improve relevance to the target role
- strengthen ATS-oriented terminology when supported by the source information
- produce a professional summary
- normalize information into the canonical schema

## AI Restrictions

The AI must not invent:

- employers
- job titles
- employment dates
- education
- certifications
- projects
- skills unsupported by the source material
- numerical achievements
- responsibilities presented as factual experience without evidence

The primary rule is:

Improve expression; never invent evidence.

## Source of Truth

The customer's supplied CV and additional information are the factual source of truth.

The AI-generated CV is a proposed optimized representation and remains subject to validation and human review during the MVP.

## Structured Output

AI responses must conform to the canonical CV schema.

The application must validate the response with Pydantic before it can be persisted or rendered.

Invalid provider output must be treated as an AI processing failure rather than silently accepted.

## Provider Abstraction

Application code must interact with an internal AI service interface.

Provider-specific concerns such as:

- API keys
- model names
- request parameters
- retry behavior
- provider response objects
- token usage metadata

must remain inside the provider implementation.

## Privacy

Customer CV content must not be written to normal application logs.

AI requests containing customer CV content should disable optional provider-side response storage where supported.

API credentials must be loaded from secure configuration and must never be committed to Git.

## Model Selection

The model must be configurable rather than hard-coded throughout the application.

Initial model selection will be based on:

- structured-output reliability
- CV rewriting quality
- latency
- cost per order

We will benchmark models using representative CV samples before production launch.

## Alternatives Considered

### Free-Form AI Text

Rejected because downstream parsing and rendering would be unreliable.

### JSON Mode Only

Rejected because valid JSON alone does not guarantee adherence to the canonical CV schema.

### Direct OpenAI Calls Throughout the Application

Rejected because it would tightly couple business logic to one provider and make testing more difficult.

### AI-Generated PDF

Rejected because visual document generation should remain deterministic and separate from content generation.

### AI Agents

Rejected for the MVP because the workflow is deterministic and does not currently require autonomous tool selection or multi-agent orchestration.

## Consequences

### Benefits

- predictable output structure
- easier automated testing
- canonical schema enforcement
- provider isolation
- lower migration cost if models/providers change
- better privacy controls
- deterministic downstream rendering

### Trade-offs

- provider adapter code must be maintained
- structured-output schemas must remain compatible with the canonical model
- model behavior still requires evaluation even when schema compliance is guaranteed
- AI quality and factual faithfulness require application-level testing

## Future Review

Revisit this decision if:

- another provider materially improves quality or cost
- production evaluation reveals structured-output limitations
- the workflow requires tool calling
- customer demand justifies more automated revision workflows
