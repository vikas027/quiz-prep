# Question File Format

Quiz question banks are plain YAML files. Upload them via the web UI, import via CLI, or use the API.

## Full example

```yaml
---
quiz_name: "CKS"
questions:
  - question: Which admission controller validates that a Pod's security context meets the cluster policy?
    choices:
      - A. PodSecurity
      - B. NodeRestriction
      - C. ResourceQuota
      - D. LimitRanger
    answer: A. PodSecurity
    category: Security
    explanation: >-
      The PodSecurity admission controller enforces Pod Security Standards
      (Privileged, Baseline, Restricted) at the namespace level, replacing
      the deprecated PodSecurityPolicy.

  - question: What does the `--anonymous-auth=false` flag on the kubelet do?
    choices:
      - A. Disables anonymous read access to the API server
      - B. Rejects unauthenticated requests to the kubelet API
      - C. Prevents pods from running as anonymous service accounts
      - D. Blocks access to the metrics endpoint
    answer: B. Rejects unauthenticated requests to the kubelet API
    category: Cluster Hardening
```

## Fields

| Field | Required | Notes |
|-------|----------|-------|
| `quiz_name` | Yes | Display name shown in the UI picker. The URL slug is derived from it (`"AWS SA"` → `aws-sa`). |
| `questions` | Yes | List of question objects. |
| `question` | Yes | The question text. |
| `choices` | Yes | 2–4 options, each prefixed `A.` `B.` `C.` `D.` |
| `answer` | Yes | Must match one of the choices exactly. |
| `category` | No | Groups questions for filtering. Omit to leave uncategorised. |
| `explanation` | No | Shown after answering. Omit if not needed. |
| `choice_explanations` | No | Dict mapping choice letter (`A`, `B`, …) to per-choice explanation. Shown inline after live feedback. |
| `disabled` | No | `true` to exclude the question from quizzes by default. The question stays in the bank and can be shown explicitly with the "All" or "Disabled only" filter. |

## Disabling questions

Mark a question with `disabled: true` when you know the answer well and want to stop seeing it in regular runs, without deleting it. You can still access it by selecting **Disabled only** or **All** in the quiz settings.

```yaml
  - question: What is the default namespace in Kubernetes?
    choices:
      - A. kube-system
      - B. default
      - C. kube-public
      - D. kube-node-lease
    answer: B. default
    category: Foundations
    disabled: true
```

You can also disable/re-enable questions:

- **During a quiz** (Live feedback mode): a "Never show again" button appears after answering.
- **Results screen**: each question in the review has a **⊘ Disable** / **↩ Enable** toggle.
- **Via API**: `PUT /api/v1/quizzes/{name}/questions/{id}` with `{"disabled": true}`.
- **Via MCP**: `manage_question(action="update", question_id=…, disabled=True)`.
- **Via YAML**: set `disabled: true` in the file and re-import.

## Without optional fields

```yaml
---
quiz_name: "Quick Practice"
questions:
  - question: Which kubectl command shows resource usage per node?
    choices:
      - A. kubectl describe nodes
      - B. kubectl top nodes
      - C. kubectl get nodes -o wide
      - D. kubectl stats nodes
    answer: B. kubectl top nodes
```

## Legacy format (plain list)

The `quiz_name` wrapper is optional. A plain list is also valid — the quiz name and slug are derived from the filename in this case.

```yaml
---
- question: What is the default namespace in Kubernetes?
  choices:
    - A. kube-system
    - B. default
    - C. kube-public
    - D. kube-node-lease
  answer: B. default
  category: Foundations
```
