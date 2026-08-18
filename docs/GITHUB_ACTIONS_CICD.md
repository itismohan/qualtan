# QUALTAN GitHub Actions CI/CD Guide

The active automation workflow is [`.github/workflows/ci-cd.yml`](../.github/workflows/ci-cd.yml). It turns the repository’s local validation command into a repeatable GitHub Actions pipeline and adds a protected deployment job for Kubernetes-based environments.

> **Safety model:** Pull requests and pushes only validate and package. Deployment is a manually dispatched workflow operation protected by GitHub Environments. No deployment occurs until an authorized operator selects `staging` or `production` and the environment supplies the required configuration.

## Pipeline behavior

| Trigger | Jobs | External side effect |
|---|---|---|
| Pull request targeting `main` | `validate` | None. Validation evidence is uploaded as an Actions artifact. |
| Push to `main` | `validate` then `package` | Publishes an immutable source bundle with a SHA-256 checksum as an Actions artifact. It does not deploy. |
| Manual dispatch with `deploy_environment=staging` or `production` | `validate` then `deploy` | Applies the selected repository Kustomize path and waits for the configured Deployment rollout. |

The `validate` job installs Python dependencies, executes `scripts/validate_framework.py`, runs committed Playwright tests when present, runs the Locust scenario against an ephemeral local REST/GraphQL mock API, performs advisory scans without blocking delivery, and uploads local validation/test output. The immutable `package` job creates a Git archive of the exact validated commit and writes a SHA-256 checksum beside it.

## Required GitHub configuration

No external performance-test URL is required for CI. The committed Locust scenario runs through `scripts/run_performance_smoke.py`, which starts and tears down an ephemeral loopback REST/GraphQL mock server. Run any real staging performance operation separately through QUALTAN’s approval-gated runtime policy, not during ordinary build validation.

Create the `staging` and `production` GitHub Environments under **Settings → Environments**. Configure required reviewers for both, with additional reviewers for production. Limit the production environment to the `main` branch and do not permit self-approval.

| GitHub Environment setting | Type | Purpose |
|---|---|---|
| `KUBE_CONFIG_DATA` | Secret | Base64-encoded kubeconfig for a least-privilege deployment identity. Keep this environment-scoped, never repository-scoped. |
| `K8S_NAMESPACE` | Variable | Kubernetes namespace containing the deployment, for example `qualtan-staging`. |
| `K8S_KUSTOMIZE_PATH` | Variable | Repository-relative Kustomize directory, for example `deploy/overlays/staging`. |
| `K8S_DEPLOYMENT` | Variable | Deployment name to verify, for example `qualtan-api`. |
| `K8S_CONTAINER` | Variable | Container name whose image may be changed when an explicit `image_tag` is supplied. |

The current repository does not include a `deploy/` or Kustomize directory. Add version-controlled manifests before enabling deployment. This is intentional: the workflow fails closed if `K8S_KUSTOMIZE_PATH` is absent or does not exist.

## Preparing Kubernetes access

The deployment identity should have only the permissions needed to apply and read the selected namespace resources and to inspect rollout status. Do not use a cluster-admin kubeconfig. Use a dedicated service account per environment; restrict namespaces, verbs, and resource kinds using RBAC; and rotate the credential on a defined schedule.

Generate the GitHub Environment secret locally from an approved kubeconfig only. The following command prints a base64 representation suitable for the `KUBE_CONFIG_DATA` secret; do not paste it into a shell history shared with other users.

```bash
base64 < ./qualtan-deployer.kubeconfig | tr -d '\n'
```

Where a cloud provider supports GitHub OIDC workload identity, replace the static kubeconfig configuration step with the provider’s OIDC login action. Keep the same GitHub Environment review gate and least-privilege Kubernetes service account.

## Deployment operation

1. Open **Actions → QUALTAN CI/CD → Run workflow**.
2. Select `main` and choose `staging` or `production` as the deployment environment.
3. Leave `image_tag` blank to apply only the version-controlled Kustomize manifests, or provide a **fully immutable image digest** such as `registry.example.com/qualtan-api@sha256:<digest>`.
4. GitHub Environment reviewers approve the deployment.
5. The job validates settings, configures `kubectl`, applies Kustomize, optionally sets the specified image, and waits up to five minutes for the rollout.
6. Review the `kubectl` rollout output and the workflow artifact before closing the change record.

The workflow serializes deployments per environment. A staging deployment cannot cancel an already executing staging deployment; a production deployment cannot run concurrently with another production deployment.

## Rollback

If the post-deployment checks or operational monitoring identify a regression, use the deployment revision history for an immediate rollback:

```bash
kubectl -n "$K8S_NAMESPACE" rollout undo deployment/"$K8S_DEPLOYMENT"
kubectl -n "$K8S_NAMESPACE" rollout status deployment/"$K8S_DEPLOYMENT" --timeout=5m
```

Then record the rollback, quarantine the failed image digest, and investigate the validation and runtime evidence. Do not bypass the QUALTAN approval, host allowlist, or external-mutation controls to accelerate incident recovery.

## Hardening backlog

| Priority | Enhancement | Reason |
|---|---|---|
| High | Add Kustomize base/overlays and resource-policy checks | The deployment job must apply reviewed, environment-specific infrastructure. |
| High | Replace static kubeconfig with cloud OIDC workload identity | Removes long-lived GitHub-held cluster credentials. |
| High | Add an image build and registry-publish job after a supported runtime service and Dockerfile are committed | The present repository is CLI/framework-oriented and has no deployable service container. |
| Medium | Generate an SBOM and attach it to the framework bundle | Improves supply-chain review and release auditability. |
| Medium | Make advisory scans blocking after dependency remediation baseline is established | Avoids shipping known high-severity dependency vulnerabilities. |
| Medium | Add deployment smoke tests against an approved staging endpoint | Confirms the deployed service, not only the code and manifest. |

## Local parity

Run the same primary framework validation before opening a pull request:

```bash
python3 scripts/validate_framework.py
```

The script deliberately excludes live Jira, X-Ray, model-provider, browser-target, and deployment operations. Those actions remain approved runtime operations rather than build-time defaults.
