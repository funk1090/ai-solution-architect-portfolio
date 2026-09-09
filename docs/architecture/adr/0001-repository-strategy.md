# ADR-0001: Repository strategy (monorepo)

## Status
Accepted

## Context
The project is conceived as an engineering portfolio built incrementally
over roughly 12 months across 7 phases, each associated with a distinct
technical project (synthetic data generator, ingestion pipeline,
requirement classifier, RAG engine, performance lab, document
understanding, and the final integrated product).

Two strategies were available for organizing the code on GitHub:

1. **Multi-repo**: one independent repository per project/phase.
2. **Monorepo**: a single repository with all projects organized as
   modules/folders within a shared structure.

This project is developed by a single person, with the explicit goal of
building a coherent professional narrative ("end-to-end enterprise AI
platform") rather than a collection of disconnected scripts.

## Decision
A **monorepo** strategy is adopted. All projects from the different
phases will live inside a single repository
(`ai-solution-architect-portfolio`), organized by functional domain
(`backend/`, `infrastructure/`, `docs/`, etc.) rather than by
chronological phase.

If, in the future, a specific component (for example, the RAG engine)
reaches enough maturity and complexity to warrant an independent release
cycle, its extraction into its own repository will be evaluated through
a new ADR.

## Alternatives considered

**Multi-repo**
- Advantages: full isolation between projects, cleaner per-project commit
  history, closer to how it would look in an organization with multiple
  teams.
- Disadvantages: duplicated configuration (CI/CD, Docker, linting),
  friction when sharing common code (e.g. logging or configuration
  utilities), and a fragmented portfolio narrative — a recruiter would
  need to navigate 7 separate repositories to understand the full
  project.

**Monorepo**
- Advantages: a single source of truth, shared configuration (linting,
  CI/CD, a Docker Compose file orchestrating all services together), a
  unified "platform" narrative, and easier maintenance for a solo
  developer without a dedicated DevOps team.
- Disadvantages: commit history mixes all domains together, and if the
  project were to grow with multiple external contributors, it might
  require additional monorepo tooling (Nx, Turborepo, Bazel) that today
  would be over-engineering for this context.

## Consequences
- Every new phase will be developed as a folder/module within this
  repository, not as a new repository.
- The root `docker-compose.yml` will be able to orchestrate services from
  all phases together, enabling end-to-end demos.
- Discipline must be maintained in organizing by domain (not mixing
  business logic from one phase with another) so the monorepo doesn't
  turn into a disorganized folder.
- This decision will be revisited if the project gains external
  contributors or if any component requires a fully independent
  deployment cycle.

## References
- Fundamentals of Data Engineering (Reis & Housley) — Ch. 3, Designing
  Good Data Architecture.
- "Architecture Before Code" principle defined in the project's
  collaboration context.
