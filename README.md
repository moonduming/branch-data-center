# Banking Data Operations & Approval Workflow Backend

**Python · Django REST Framework · MySQL · Celery · Redis · Docker**

## Project overview

This backend connects branch data ingestion, performance indicator calculations, employee performance attribution, and approval workflows in a banking operations context. It illustrates backend patterns that also apply to internal tools, reporting platforms, and business process automation.

The business flow is straightforward: import dated source files, track processing status, check data dependencies, calculate business indicators, expose dashboard APIs, and route performance claim or transfer requests through configurable approval steps.

## Technical scope

- **REST APIs:** JWT authentication, user administration, organization structures, employee assignments, filtering, pagination, and consistent response handling.
- **Data pipelines:** Scheduled and manual imports, per-file processing records, configurable retry limits, upstream dependency checks, and a host-side integration adapter for bulk loading.
- **Business calculations:** Versioned SQL templates, date and organization parameters, indicator results, and employee results after profit allocation.
- **Workflow automation:** Configurable processes, nodes, transitions, assignee rules, task handling, withdrawal, work queues, and activity logs.
- **Deployment tooling:** Separate web, worker, and scheduler processes; Redis messaging; container builds; and offline image delivery scripts.

## Implementation decisions

**Working with an existing database.** Unmanaged Django models map business tables maintained through SQL scripts. This is useful when integrating a Python service with an established reporting schema.

**Keeping long-running work outside HTTP requests.** Celery handles import and calculation jobs. Import logs and dependency checks make processing state visible to operators.

**Separating workflow configuration from execution.** Definition models describe processes, nodes, transitions, and assignment rules. A runtime service manages instances, tasks, and business activity records, with transaction boundaries around workflow operations.

**Testing business behavior.** Tests cover API and serializer behavior, import orchestration, performance requests, backups, and workflow execution. Mocked tests support development; live database and end-to-end deployment validation are separate activities.

## Relevance to client projects

This project is a useful code example for Django backend development, REST API integrations, Celery job processing, legacy MySQL integration, reporting backends, and configurable approval systems.

### Short project summary for a proposal

> A relevant project example is a Django backend for banking data operations. It connects scheduled imports and SQL-based indicator calculations with REST APIs, employee performance attribution, and configurable approval workflows. The implementation uses MySQL, Celery, Redis, JWT authentication, and Docker, with separate modules for data processing and workflow execution. These patterns are directly relevant to internal systems that need background jobs, reporting APIs, and approval tasks.

## Repository guide

The source is organized into `apps/users`, `apps/organization`, `apps/datahub`, `apps/performance`, and `apps/workflow`. Shared API behavior lives in `common/`; deployment settings live in `config/`. Start with `config/urls.py`, `apps/workflow/runtime.py`, and `apps/datahub/services/`.

The repository contains the backend; API messages and business labels are primarily in Chinese. Runtime credentials and business datasets are supplied privately.

Detailed API documentation (Chinese):

- [Users and authentication](docs/users-api.md)
- [Organization and employee assignments](docs/organization-api.md)
- [Data imports and indicators](docs/datahub-api.md)
- [Performance attribution](docs/performance-api.md)
- [Approval workflows](docs/workflow-api.md)

This description covers implemented functionality without claiming measured performance, compliance certification, or an individual contributor's role. Adapt the proposal summary to your actual contribution.
