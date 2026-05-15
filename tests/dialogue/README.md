# Dialogue scenario assets

These JSON scenarios replay multi-turn user utterances through `detect_intent()` and the follow-up/dialogue resolution layer without calling system routers or external services.

## Metrics

The offline evaluator reports these gate metrics:

- **Intent accuracy**: percentage of turns whose `detect_intent()` result matches `expect.intent`.
- **Slot fill accuracy**: percentage of expected slot key/value pairs found in the detected intent payload or, when specified, the dialogue command payload.
- **Context carry-over success**: percentage of turns marked with `expect.context_carryover: true` that were resolved from carried dialogue context (for example `source: context_followup`, a temporal follow-up flag, or an expected dialogue command produced from pending state).
- **Clarification appropriateness**: percentage of turns with `expect.clarification` whose dialogue result asks for, avoids, or resolves clarification as expected.

Run locally with:

```bash
python tests/dialogue/evaluate_dialogues.py
```
