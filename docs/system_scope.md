| Category              | Meaning                                                       | Example symptom                                           |Required evidence      |
| --------------------- | ------------------------------------------------------------- | --------------------------------------------------------- | ------- |
| `dns_failure`         | A service name cannot be resolved                             | Requests fail because `payment` cannot be resolved        |DNS-related Kubernetes event or failed DNS lookup |
| `service_routing`     | A Kubernetes Service has no usable endpoints                  | `checkout` returns HTTP 503 although its pods are running | Endpoint count is zero while the relevant pods are healthy |
| `dependency_failure`  | An upstream service fails because a dependency is unavailable | `checkout` fails because `payment` is down                | A dependency is unhealthy while the investigated service is otherwise healthy |
| `latency_degradation` | Request latency increases significantly                       | Checkout p95 latency rises from 200 ms to 2 seconds       | p95 latency is substantially above its normal baseline |
| `http_error_increase` | The proportion of 5xx responses increases                     | `frontend` begins returning many HTTP 500 responses       | 5xx error rate is substantially above its normal baseline |
| `resource_saturation` | CPU or memory pressure affects service performance            | High CPU causes increased latency and errors              | CPU or memory is high and the degradation occurs during the same time window |

## Evidence sources

| Source | Information |
|---|---|
| Documentation retrieval | Kubernetes documentation and internal runbooks |
| Metrics | Error rate, latency, CPU, memory, endpoint count, request rate |
| Kubernetes events | DNS failures, readiness failures, selector changes, pod restarts |

## Evidence states

### `evidence_sufficient`

The evidence supports a specific probable cause.

### `evidence_partial`

The evidence suggests one or more causes, but does not distinguish between them reliably.

### `insufficient_evidence`

The required observations are missing or contradictory.

## Non-goals

Version 1 will not:

- modify a Kubernetes cluster;
- execute shell commands;
- restart or reconfigure services;
- diagnose incidents outside the six supported categories;
- use confidential company data;
- perform automatic remediation;
- train an anomaly-detection model;
- use multiple AI agents.