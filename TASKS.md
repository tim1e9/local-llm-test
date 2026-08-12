# Tasks - HR Vacation Application

## Priority 1: Project Setup & Foundation
- [x] Task 1: Create project structure (backend/, frontend/ directories)
- [x] Task 2: Create Python virtual environment and install dependencies
- [x] Task 3: Define SQLite database schema (users, roles, vacation requests, balances)
- [x] Task 4: Implement database service layer

## Priority 2: Core Backend API
- [x] Task 5: Set up Flask application with routing structure
- [x] Task 6: Implement OAuth/OIDC authentication framework (token verifier, auth service)
- [x] Task 7: Implement role-based access control (EMPLOYEE, MANAGER, ADMIN)
- [x] Task 8: Create vacation request CRUD endpoints

## Priority 3: Business Logic
- [x] Task 9: Implement vacation balance tracking
- [x] Task 10: Implement manager approval/rejection workflow
- [x] Task 11: Add validation rules (date ranges, balance checks)

## Priority 4: Frontend
- [x] Task 12: Create HTML pages (login callback, dashboard, request form, approvals)
- [x] Task 13: Create CSS styling
- [x] Task 14: Implement JavaScript for API communication and UI interactivity

## Priority 5: Polish & Integration
- [x] Task 15: Create .env configuration file
- [x] Task 16: Test the application end-to-end
- [ ] Task 17: Add admin user management endpoints

## Bug Fixes
- [x] Fix "My Balance" tab showing `undefined`/`NaN` for users without balance records (empty `{}` was treated as truthy)
- [ ] Fix remaining issues discovered during e2e testing
