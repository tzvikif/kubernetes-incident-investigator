# Kubernetes DNS Failure

## Symptoms

A service may fail to contact another service because the dependency's hostname cannot be resolved.

## Relevant evidence

Check:

- failed DNS lookup results;
- Kubernetes events containing DNS resolution errors;
- the health of the destination service and its Pods;
- whether the destination Service has available endpoints.

## Supported diagnosis

A failed DNS lookup or a DNS-related Kubernetes event supports a DNS-failure diagnosis.

If the destination service is healthy and has available endpoints, this further distinguishes DNS failure from dependency failure or service-routing failure.

## Diagnostic boundaries

A connection failure alone does not prove a DNS failure.

Do not report DNS failure unless a failed DNS lookup, DNS-related event, or equivalent direct evidence is available.

If DNS evidence is missing, classify the available evidence as partial or insufficient.