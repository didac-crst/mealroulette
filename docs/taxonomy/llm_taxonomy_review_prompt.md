# LLM Taxonomy Review Prompt

Use this prompt to review one ingredient candidate batch at a time.

```text
You are reviewing a MealRoulette ingredient taxonomy batch.

Do not rewrite the YAML.
Return only structured findings.

Review for:
- wrong food group
- wrong ingredient family
- ingredient too broad
- ingredient too specific
- likely duplicate
- missing common aliases in English, French, Spanish, or Catalan
- ambiguous aliases
- suspicious conversion factors
- pantry flag suspicious
- description unclear for resolver or LLM top-down selection
- ingredients that should be split into multiple canonical ingredients
- ingredients that should be merged

Important taxonomy model:
- ingredient = exact shopping/recipe item
- ingredient_family = similarity vector level
- food_group = broad trait/filter level

Output JSON:

{
  "summary": {
    "accepted_count": 0,
    "review_count": 0,
    "blocker_count": 0,
    "suggestion_count": 0
  },
  "findings": [
    {
      "severity": "blocker | review | suggestion | accepted",
      "ingredient": "string",
      "field": "string",
      "issue": "string",
      "recommended_change": "string",
      "rationale": "string",
      "confidence": 0.0
    }
  ]
}

Rules:
- Use blocker only for duplicate/invalid data that should not be imported.
- Use review when a human should decide.
- Use suggestion for non-blocking improvements.
- Use accepted only for rows that are clean and unambiguous.
- Do not invent exact conversion factors unless clearly standard.
- If a conversion is approximate, recommend approved: false.
- If a name is generic, prefer splitting over over-broad aliases.
```
