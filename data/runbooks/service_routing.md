# Kubernetes Service Routing

## Symptoms

A service may return HTTP 503 responses even though its Pods are healthy.

## Relevant evidence

Check:

- the number of available Service endpoints;
- the number and health of relevant Pods;
- Kubernetes events concerning selectors or endpoints.

## Supported diagnosis

If the relevant Pods are healthy but the Service has zero available endpoints,
the Service is not routing traffic to those Pods.

A selector-mismatch event can identify the specific reason that the Service has
no endpoints.

## Diagnostic boundaries

Healthy Pods and zero endpoints support a service-routing problem.

Zero endpoints alone do not prove a selector mismatch. The selector mismatch
should only be reported when an event or other direct evidence confirms it.