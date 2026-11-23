# AI Lead Triage — n8n demo

Inbound B2B leads are classified by an LLM, deduplicated, logged and routed. When the model isn't sure, a human approves first. When anything breaks, an alert goes out.

n8n 2.x · Google Gemini · Google Sheets · Gmail

## The problem
A sales inbox gets a mix of real buyers, partners, job seekers and spam. Triage by hand is slow, עצשןbecause a hot lead can wait hours. It is also inconsistent: the same lead gets logged twice, or not at all.

## How it works
1. **Form trigger.** The lead submits name, work email, company, country and a message.
2. **Normalize.** Trims fields, lowercases the email and extracts the email domain.
3. **Classify (LLM).** An Information Extractor with Gemini (temperature 0) returns `segment`, `priority`, `confidence` and `summary` as structured fields.
4. **Confidence gate.** Leads with `confidence >= 0.7` route automatically. Anything lower goes to a human through a Gmail Approve / Disapprove request, and the run waits for the answer.
5. **Upsert.** A Google Sheets *append or update* step matches on the normalized email, so a repeat submission updates the existing row instead of adding a duplicate. Every row stores the route taken and the n8n execution ID.
6. **Notify.** An email goes to the lead owner with the priority and a one-line summary.

## Failure modes and how each is handled
| What can go wrong | Handling |
|---|---|
| LLM call fails or times out | 3 retries, 2 s apart. If all fail, the node's error output sends the lead to a fallback (confidence 0), which goes to human review. The lead is never dropped. |
| Model is unsure, or the message is vague | The confidence gate sends it for human approval before routing |
| Same person submits twice, or email casing differs | The email is normalized, then upserted on email |
| Downstream failure (missing column, expired auth) | A separate error workflow (Error Trigger) emails the workflow name, the failed node, the error and a link to the execution |
| Wrong classification | Every row traces back to its execution, and approval decisions are logged for prompt tuning |

## Results from a demo run
These numbers come from [7] test leads that I wrote and labeled before running. It is a smoke test, not a benchmark.
- Segment matched my label: **[5]/[7]**
- Sent to human review: **[14]%**
- Auto-routed lead, submission to logged row: about **[4] s**
- Less than 0.1 cents per lead, roughly **$[0.64]** per lead at [Gemini 3.8 Flash] list prices (the demo ran on the free tier)
- Forced failure (broke the sheet's match column): the alert email arrived in **[5] s**, with the execution link

## KPIs I'd track in production
- Time to first response on a new lead, measured against the current manual baseline
- Routing accuracy: the share of auto-routed leads that sales didn't re-classify
- Human-review rate and approval rate, which show whether the 0.7 threshold is right
- Duplicate records created (target: 0)
- Failed runs per week, time to fix and cost per lead

## Limits, and what changes for production
- Sheets stands in for the CRM. The same flow maps to Salesforce or HubSpot with an upsert on email, either in n8n or as a Workato recipe.
- The Gemini free tier is for demo data only. Production would use a paid tier or Vertex AI so customer data stays out of model training.
- The approval request has no timeout. Production needs one, with a default route and an escalation path.
- Next steps: enrichment (company size, domain lookup) before classification, and about 50 real historical leads labeled to tune the threshold.

## Run it
1. Import `workflow.json` into n8n from the workflow menu (Import from file).
2. Add credentials: a Google Gemini API key, plus Google sign-in for Sheets and Gmail.
3. Create a Google Sheet with this header row:
   `received_at, triaged_at, name, email, company, country, message, segment, priority, confidence, summary, route, execution_id`
4. Point the Sheets and Gmail nodes at your sheet and email address.
5. Import `error-workflow.json`, publish it, select it under the main workflow's Settings → Error workflow, then publish the main workflow.
