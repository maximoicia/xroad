# X-Road Collaboration Portal

This project provides a collaborative portal for organizations that consume or provide services through an existing X-Road infrastructure. The platform focuses on simplifying operational tasks around credentials, security server configuration, and secure file exchange between members.

## Features

- **Authentication and RBAC** – OAuth2 password flow with JWT tokens, configurable admin bootstrap, and role-based access control with granular permissions for user, role, member, file, and audit log management.
- **Member directory** – Manage X-Road member metadata, including API keys and local Security Server IP addresses, so each organization can maintain their integration parameters in a central location.
- **Secure file exchange** – Upload files, share them with selected X-Road members, and download files that have been shared with your organization. Files are stored on disk with SHA-256 integrity metadata.
- **Audit logging** – Track administrative and collaboration actions across the platform.
- **Health endpoint & CORS** – Basic health probe and configurable CORS origins for integration with custom front-ends.

## Getting started

1. **Install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure environment**
   Create a `.env` file (optional) to override defaults:
   ```env
   SECRET_KEY=change-me
   ACCESS_TOKEN_EXPIRE_MINUTES=480
   INITIAL_ADMIN_USERNAME=admin
   INITIAL_ADMIN_PASSWORD=strong-password
   INITIAL_ADMIN_EMAIL=admin@example.com
   ```

3. **Run the API**
   ```bash
   uvicorn app.main:app --reload
   ```

   On first startup the application will:
   - Create required database tables.
   - Ensure default roles exist (`administrator`, `member`).
   - Bootstrap an administrator user with the configured credentials.

4. **Explore the API**
   FastAPI automatically exposes interactive documentation at `http://localhost:8000/docs` and a health check at `http://localhost:8000/health`.

## Project structure

```
app/
  config.py        # Runtime configuration via Pydantic settings
  database.py      # SQLModel engine and session helpers
  models.py        # ORM models for users, roles, members, files, audit logs
  schemas.py       # Pydantic schemas exposed by the API
  security.py      # Password hashing, JWT helpers, permission constants
  deps.py          # FastAPI dependencies (auth, RBAC)
  crud/            # Database operations grouped by domain
  routers/         # FastAPI routers for authentication, RBAC, members, files, audits
  storage/         # Local filesystem storage helpers for uploaded files
```

Uploaded files are persisted under `storage/files` by default. Adjust the `UPLOAD_DIR` setting if you require another location or external storage.

## Next steps

- Integrate with your preferred identity provider or portal UI.
- Add organization-specific metadata to the `Member` model.
- Extend audit log analysis or connect to centralized monitoring.

Contributions and adaptations are welcome for tailoring the platform to specific X-Road deployments.
