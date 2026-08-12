# Kubernetes Dependency Failure

## Symptoms

A service may fail or return errors even though its own Pods and Service endpoints are healthy.

## Relevant evidence

Check:

- the health of upstream dependencies;
- the health of the investigated service's Pods;
- the number of available Service endpoints;
- errors showing failed requests to a dependency.

## Supported diagnosis

If the investigated service is healthy and reachable, but a required dependency is unhealthy, the incident supports a dependency-failure diagnosis.

The unhealthy dependency should be identified when direct dependency-health evidence is available.

## Diagnostic boundaries

Errors in the investigated service do not by themselves prove that a dependency failed.

Do not report a dependency failure unless the relevant dependency is confirmed as unhealthy or unavailable.

If dependency-health information is missing, the evidence may be partial or insufficient.