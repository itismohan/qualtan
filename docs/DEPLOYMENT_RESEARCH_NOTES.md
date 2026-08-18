# Deployment Research Notes

## Authoritative sources consulted

1. Kubernetes Horizontal Pod Autoscaling: https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/
   - HPA scales a compatible workload such as a Deployment or StatefulSet from observed resource and custom/external metrics.
   - The autoscaling/v2 API supports multiple metrics and configurable scale-up/scale-down behavior, including stabilization to dampen flapping.
   - CPU-based autoscaling depends on resource requests being declared.

2. Kubernetes Deployments: https://kubernetes.io/docs/concepts/workloads/controllers/deployment/
   - Deployments manage declarative rollout state and provide controlled updates, rollback capability, and replica scaling.
   - Rolling updates use maxUnavailable and maxSurge controls; rollout status must be monitored.

3. Kubernetes liveness, readiness, and startup probes: https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/
   - Liveness identifies broken containers for restart.
   - Readiness keeps unready Pods out of Service traffic.
   - Startup probes protect slow initialization from premature liveness failures.

4. Kubernetes Secret good practices: https://kubernetes.io/docs/concepts/security/secrets-good-practices/
   - Secret objects are base64 encoded and unencrypted in etcd by default unless encryption at rest is configured.
   - Restrict Secret access under least privilege; avoid logging or checking secret manifests into source control.
   - External secret stores can be mounted for authorized Pods through the Secrets Store CSI Driver.

5. OpenTelemetry Python: https://opentelemetry.io/docs/languages/python/
   - The Python API and SDK support telemetry generation and collection for metrics, logs, and traces.
   - OTLP, Prometheus, Jaeger, Zipkin, and other exporters are available as installable packages.

6. Twelve-Factor App configuration: https://12factor.net/config
   - Deploy-varying configuration, credentials, backing-service handles, and canonical host names should remain separate from code.
   - Environment variables are an operating-system- and language-agnostic mechanism for deploy-specific configuration.
