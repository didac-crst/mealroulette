# CodeRabbit

This repo uses [CodeRabbit](https://coderabbit.ai/) for optional PR reviews. Configuration lives in [`.coderabbit.yaml`](../.coderabbit.yaml) at the repo root.

## Default behavior

| Setting | Value | Effect |
| --- | --- | --- |
| `auto_review.enabled` | `true` | Reviews when a PR is opened |
| `auto_review.auto_incremental_review` | `false` | Does **not** re-review every push (saves quota) |

## Commands (comment on the PR)

When you push fixes and want another review:

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

Resume automatic behavior on that PR:

```text
@coderabbitai resume
```

## Stricter option (manual-only)

If you want zero automatic reviews and only review when you ask, change `.coderabbit.yaml` to:

```yaml
reviews:
  auto_review:
    enabled: false
    auto_incremental_review: false
    description_keyword: "@coderabbitai review"
```

## Links

- [CodeRabbit configuration reference](https://docs.coderabbit.ai/guides/configure-coderabbit)
- [Review commands](https://docs.coderabbit.ai/guides/commands)
