# Kubernetes Latency Degradation

## Symptoms

A service may remain available while responding substantially more slowly than normal.

## Relevant evidence

Check:

- current p95 latency;
- historical or expected p95 latency;
- the time window during which latency increased;
- request volume and error rate;
- dependency latency and resource utilization.

## Supported diagnosis

A current p95 latency that is substantially above its normal baseline supports a latency-degradation diagnosis.

For example, an increase from a baseline of 200 ms to 2,000 ms is direct evidence of significant latency degradation.

## Diagnostic boundaries

High latency identifies performance degradation but does not, by itself, identify its root cause.

Do not attribute the degradation to resource saturation, dependency failure, or another cause without supporting evidence.

If no baseline is available, the evidence may be partial because the system cannot determine whether the observed latency is abnormal.