# Security & Roles - SAP Prognos

## Frontend Role-Based Access Control (RBAC)
The SAPUI5 frontend implements a mock Role-Based UI for demonstration purposes. 

- **Admin Role** (`admin` / `admin`): Has full access to the Dashboard, Simulator, Analytics, Inventory, and Settings pages.
- **User Role** (`user` / `user`): Restricted to view-only tasks. The `Inventory` and `Settings` pages are hidden from the navigation menu.

## Backend Security
- **CORS**: The FastAPI backend implements `CORSMiddleware`. The `allow_origins` is restricted to the specific frontend URL loaded via the `.env` file (`ALLOWED_ORIGINS`).
- **Validation**: All endpoints use Pydantic models to strictly enforce data types and constraints (e.g., `gt=0` for Store/Item IDs, `ge=0` for sales figures) to prevent injection or unexpected behavior.

> [!WARNING]
> This is a portfolio prototype. In a real-world SAP BTP implementation, authentication would be handled via SAP Cloud Identity Services, OIDC, or OAuth2 (JWT tokens) passed in the Authorization header.
