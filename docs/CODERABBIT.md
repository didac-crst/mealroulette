# CodeRabbit

This repo uses [CodeRabbit](https://coderabbit.ai/) for PR reviews **on demand only**. Configuration lives in [`.coderabbit.yaml`](../.coderabbit.yaml) at the repo root.

## Why manual-only

Reviews are triggered by you, not on PR open or push. That way a failed CI run does not consume a CodeRabbit review before the code is ready.

**Typical flow:** open PR → fix until CI is green → comment `@coderabbitai review`.

## Commands (comment on the PR)

Request a review when CI passes and you are ready:

```text
@coderabbitai review
```

Full re-review from scratch:

```text
@coderabbitai full review
```

Pause reviews on one PR while you work:

```text
@coderabbitai pause
```

Resume:

```text
@coderabbitai resume
```

## Current config

```yaml
reviews:
  auto_review:
    enabled: false
    auto_incremental_review: false
```

On public GitHub repos, CodeRabbit only applies `.coderabbit.yaml` from the **default branch** until it is merged to `main`.

## Optional: review on PR open (not recommended here)

If you prefer one automatic review when opening a PR but no re-review on every push:

```yaml
reviews:
  auto_review:
    enabled: true
    auto_incremental_review: false
```

## Links

- [CodeRabbit configuration reference](https://docs.coderabbit.ai/guides/configure-coderabbit)
- [Review commands](https://docs.coderabbit.ai/guides/commands)
