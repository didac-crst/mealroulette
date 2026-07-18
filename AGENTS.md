# [AGENTS.md](http://AGENTS.md)

## Purpose

This repository is developed through an AI-assisted workflow with explicit

separation between product reasoning, architecture, implementation and review.

The human owner is the final authority on product behaviour, scope and

architecture.

## Sources of truth

Before proposing or making changes, read:

- `README.md`;

- [docs/README.md](docs/README.md) — documentation authority map;

- the documents referenced by the current task;

- the architecture, specification and ADR documents relevant to the affected

  area under `docs/`;

- the existing tests and implementation relevant to the requested behaviour.

In Architecture mode, inspect the broader documentation and implementation

when needed to identify cross-cutting constraints.

When documentation, tests and implementation disagree, do not silently choose

one as authoritative. Report the conflict and explain its implications.

## Default tool responsibilities

The repository normally uses the following workflow:

- **ChatGPT** supports product exploration and helps the human owner clarify

  requirements, alternatives and intended behaviour outside the repository.

- **Codex** defaults to Architecture mode. It is primarily responsible for

  repository analysis, architecture proposals, specifications, ADRs, roadmaps,

  acceptance criteria and implementation planning.

- **Cursor** defaults to Implementation mode. It is primarily responsible for

  implementing approved specifications, updating tests and documentation, and

  running the relevant validation commands.

- **CodeRabbit** provides the default external Review-mode feedback on GitHub

  pull requests.

- **The human owner** makes final product and architecture decisions, resolves

  disputed recommendations and approves completion.

These assignments are defaults, not capability restrictions. An explicit

instruction in the current task may assign a different work mode to a tool.

Do not infer permission to move from one mode to another merely because the

next step appears obvious.

In particular:

- Codex must not implement an architecture or specification unless explicitly

  asked to enter Implementation mode.

- Cursor must not silently redesign an approved specification while

  implementing it.

- Review findings must not be applied blindly. Assess each finding against the

  specification, architecture, documented invariants and current code.

## Work modes

### Architecture mode

Use this mode when asked to analyse, design, create specifications, define

behaviour or update the roadmap.

Responsibilities:

- Understand the existing implementation before proposing changes.

- Identify assumptions, alternatives, trade-offs and failure modes.

- Prefer the simplest reversible design that solves the current problem.

- Distinguish current requirements from hypothetical future requirements.

- Avoid designing for speculative needs without concrete evidence.

- Record important decisions as ADRs.

- Define domain invariants, state transitions and acceptance criteria.

- Identify migration, compatibility and rollback implications.

- Propose appropriate unit, integration and end-to-end test scenarios.

- Make unresolved product and architecture decisions visible.

- Do not modify production code unless explicitly requested.

Architecture output should distinguish clearly between:

- confirmed requirements;

- assumptions;

- recommendations;

- rejected alternatives;

- unresolved decisions;

- future possibilities that are intentionally out of scope.

### Implementation mode

Use this mode when implementing an approved specification or clearly defined

change.

Responsibilities:

- Read the referenced specification and relevant ADRs first.

- Follow the approved architecture and documented product semantics.

- Inspect the affected implementation and tests before making changes.

- Make the smallest coherent change that satisfies the specification.

- Do not introduce speculative abstractions, features or unrelated

  refactoring.

- Do not silently change product semantics.

- Do not resolve material ambiguity by choosing the most convenient

  implementation.

- Update tests and documentation together with behavioural changes.

- Run the relevant validation commands before declaring completion.

- State any remaining risks, limitations or unverified assumptions.

If implementation reveals an unresolved product or architecture decision:

1. stop the affected part;

2. explain the conflict or ambiguity;

3. describe its practical consequences;

4. list realistic alternatives;

5. recommend one;

6. wait for a human decision unless the specification explicitly permits a

   safe and reversible default.

Unrelated parts of the task may continue when they do not depend on the

unresolved decision.

### Review mode

Use this mode when reviewing code, a branch, a commit or a pull request.

Responsibilities:

- Review against the specification, ADRs, documented invariants and intended

  product behaviour.

- Inspect the actual implementation before accepting or rejecting a finding.

- Look for incorrect behaviour, regressions, data-integrity problems,

  security issues, concurrency issues, unsafe migrations and missing tests.

- Check whether implementation, tests and documentation remain aligned.

- Distinguish blockers, valid improvements and optional suggestions.

- Avoid stylistic churn that provides no material benefit.

- Do not assume that passing tests prove that the product decision is correct.

- Do not redesign the feature unless the current design creates a material

  correctness, security or maintainability problem.

- Identify false positives and outdated findings explicitly.

## Decision principles

- Prefer simple, reversible solutions.

- Solve the current concrete problem before generalising.

- Do not generalise before a demonstrated need exists.

- Avoid speculative features and premature abstractions.

- Preserve canonical domain concepts independently from presentation, locale

  or external integrations.

- Treat database constraints and domain invariants as part of the design.

- Make state transitions explicit.

- Preserve historical data semantics.

- Consider migration, compatibility and rollback for persistent-data changes.

- Prefer explicit behaviour over hidden conventions.

- Prefer changes that are easy to understand, test and remove.

- Separate current requirements from possible future extensions.

- Use observed behaviour and real product usage to validate assumptions.

## Testing expectations

For behavioural changes:

- add or update unit tests for domain rules;

- add integration tests for persistence and component interaction;

- add end-to-end tests only for critical user workflows;

- test failure modes and boundary conditions, not only happy paths;

- test relevant state transitions and historical-data behaviour;

- ensure tests reflect the specification rather than merely mirroring the

  implementation;

- verify that tests would fail when the intended behaviour is broken.

Never weaken, skip or delete a test solely to make a change pass.

When an existing expectation is obsolete:

1. explain why it is obsolete;

2. identify the product or architecture decision that changed;

3. update the corresponding specification or ADR;

4. update the test to reflect the approved behaviour.

Generated tests are not considered independent validation when they merely

restate the implementation. Review whether they meaningfully exercise the

required behaviour and failure cases.

## Documentation expectations

Documentation must describe the behaviour that is actually approved and

implemented.

For material changes, update the relevant combination of:

- feature specifications;

- ADRs;

- architecture documentation;

- roadmap or task status;

- migration notes;

- operational instructions;

- user-facing documentation.

Do not duplicate the same decision across several documents unless each copy

has a clear purpose.

When documents conflict, resolve the conflict or report it explicitly rather

than adding another interpretation.

## Completion criteria

A task is complete only when:

- the approved behaviour is implemented;

- relevant tests pass;

- linting, formatting, type checking and static analysis pass where configured;

- documentation reflects the result;

- migrations are safe and documented where applicable;

- validation commands have been run and their results reported;

- no known conflict with existing requirements remains;

- remaining risks, limitations and assumptions are stated explicitly;

- no unrelated or speculative scope has been introduced.

A task is not complete merely because:

- code was generated;

- the application starts;

- the happy path works;

- tests written by the same agent pass;

- the diff appears structurally clean.

## Human authority

The agent may recommend product and architecture decisions, but must not

silently make irreversible, security-sensitive or materially scope-expanding

decisions.

The human owner approves:

- product semantics;

- architecture changes;

- new production dependencies;

- destructive or difficult-to-reverse migrations;

- security-sensitive behaviour;

- major scope expansion;

- changes that invalidate an approved specification or ADR;

- acceptance of significant known risk.

Safe, local and reversible implementation details may be selected by the agent

when they do not materially affect product behaviour or architecture.

## Pull-request review workflow

### Branch size and review checkpoints

When a branch reaches roughly **40-50 modified files**, pause before expanding

the scope further.

At that point, prefer one of these actions:

- split the remaining work into a follow-up branch;

- open a pull request for external review, even if it will not be merged

  immediately;

- ask the human owner whether the current scope should continue as one PR.

This is a reviewability checkpoint, not a hard merge requirement. Do not create

artificially tiny or incoherent slices just to satisfy a file count, and do not

merge incomplete work merely because a PR was opened.

Unless the current request clearly states otherwise, phrases such as:

- “read the review”;

- “check the review”;

- “address the review”;

- “look at what CodeRabbit found”;

refer to the CodeRabbit review associated with the relevant GitHub pull

request, not to a new local review generated by the current agent.

When asked to read or check the review:

1. identify the relevant GitHub pull request;

2. retrieve the current CodeRabbit review summary;

3. retrieve CodeRabbit inline comments and unresolved review threads;

4. account for later CodeRabbit updates made after new commits;

5. distinguish unresolved findings from resolved, outdated, duplicated or

   superseded comments;

6. inspect the referenced code before accepting a finding;

7. classify each relevant finding as:

   - blocker;

   - valid improvement;

   - optional suggestion;

   - false positive;

   - already resolved;

   - outdated or superseded;

8. explain the proposed response before making product-level or architectural

   changes.

When a finding is valid and compatible with the approved specification,

implementation-level corrections may be applied without requiring a new

architecture decision.

When a finding implies a change to product semantics, architecture, persistent

data behaviour, security policy or approved scope, report it for human

decision before implementing it.

Do not treat CodeRabbit comments as authoritative requirements. Approved

specifications, ADRs, documented invariants and human decisions remain

authoritative.

If multiple pull requests could be relevant and the current branch or task

does not identify one unambiguously, report the candidates instead of

selecting one silently.

If GitHub or the pull-request review is not accessible from the current

environment, state that clearly. Do not pretend to have read the review based

only on local code, commit messages, cached information or previous summaries.
