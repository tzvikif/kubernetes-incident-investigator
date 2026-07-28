| Category              | Meaning                                                       | Example symptom                                           |
| --------------------- | ------------------------------------------------------------- | --------------------------------------------------------- |
| `dns_failure`         | A service name cannot be resolved                             | Requests fail because `payment` cannot be resolved        |
| `service_routing`     | A Kubernetes Service has no usable endpoints                  | `checkout` returns HTTP 503 although its pods are running |
| `dependency_failure`  | An upstream service fails because a dependency is unavailable | `checkout` fails because `payment` is down                |
| `latency_degradation` | Request latency increases significantly                       | Checkout p95 latency rises from 200 ms to 2 seconds       |
| `http_error_increase` | The proportion of 5xx responses increases                     | `frontend` begins returning many HTTP 500 responses       |
| `resource_saturation` | CPU or memory pressure affects service performance            | High CPU causes increased latency and errors              |
