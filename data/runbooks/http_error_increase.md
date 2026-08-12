# Kubernetes HTTP Error Increase

## Symptoms

A service may remain reachable while returning substantially more HTTP 5xx responses than normal.

## Relevant evidence

Check:

- the current HTTP 5xx error rate;
- the historical or expected 5xx error-rate baseline;
- the time window during which errors increased;
- request volume;
- latency, resource utilization, and dependency health.

## Supported diagnosis

An HTTP 5xx error rate substantially above its normal baseline supports an HTTP-error-increase diagnosis.

For example, an increase from a baseline of 1% to 20% is direct evidence of a significant increase in server errors.

## Diagnostic boundaries

An increased HTTP 5xx rate identifies service degradation but does not, by itself, identify its root cause.

Do not attribute the errors to resource saturation, dependency failure, or another cause without supporting evidence.

If no error-rate baseline is available, the evidence may be partial because the system cannot determine whether the observed rate is abnormal.