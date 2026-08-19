# Support

## Where to ask for help

Use the appropriate public channel so that answers remain discoverable and maintainers can triage effectively.

| Need | Recommended route | Do not include |
|---|---|---|
| Usage question, design discussion, or implementation idea | GitHub Discussions, once enabled | Credentials, customer data, internal URLs, or production evidence |
| Reproducible defect | GitHub bug-report issue form | Vulnerability details or unredacted sensitive logs |
| Feature or integration request | GitHub feature-request issue form | Commitments to external vendor behavior without documentation |
| Suspected vulnerability | Private vulnerability reporting | Any public issue, discussion, or pull request |
| Conduct concern | Private contact route to a maintainer | Public retaliation or personal data |

## Before requesting support

Run the diagnostic and local verification commands from the repository root. Attach only the minimum redacted output required to reproduce the issue.

```bash
python3 cli/main.py doctor
pytest -q tests
python3 scripts/validate_framework.py
```

For browser mocks, install the documented Node.js dependencies and run `CI=1 npm run test:mocks`. For the Locust smoke runner, install `requirements.txt` in the active Python environment first.

## Community expectations

Community support is provided on a best-effort basis by maintainers and contributors. It does not include response-time guarantees, production incident management, custom implementation work, or review of secrets and proprietary customer data. Follow [`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) in every project channel.

## Enterprise and managed operations

The community edition is designed to operate locally with explicit policies and approvals. A future managed offering may provide centralized policy administration, audit retention, enterprise identity integration, fleet operations, and commercial support. Such a service must complement—not disable or replace—the open governed core.
