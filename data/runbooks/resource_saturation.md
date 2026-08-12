# Kubernetes Resource Saturation

## Symptoms

A service may experience increased latency or errors when its containers are under sustained CPU or memory pressure.

## Relevant evidence

Check:

- CPU and memory utilization;
- CPU throttling or out-of-memory events;
- latency and HTTP error rates;
- historical latency and error-rate baselines;
- whether resource pressure and degradation occurred during the same time window.

## Supported diagnosis

High CPU or memory utilization combined with concurrent performance degradation supports a resource-saturation diagnosis.

A CPU-throttling event provides direct evidence that CPU limits affected the service.

## Diagnostic boundaries

High latency or an increased error rate alone does not prove resource saturation.

High CPU or memory utilization without concurrent service degradation may not represent an incident.

Do not identify resource saturation as the cause unless resource pressure and performance degradation occurred during the same time window.