# Skill: Professional Verification Workflow

## Overview
This skill implements the end-to-end professional verification flow in BuscaMedicos. It ensures that medical professionals are verified by an administrator before their profiles correctly transition to an active/public state.

## Architecture
- **Backend Model**: Uses `VerificationRequest` and `ProfessionalDocument`.
- **Storage**: Real file storage at `/app/files` with soft-delete capabilities.
- **Frontend**: Dedicated profile management page at `/professional/profile` and admin review dashboard at `/admin/validation/requests`.

## Key Components

### 1. Professional Onboarding (`/professional/profile`)
- Professionals must complete their public profile (name, type, bio).
- **Mandatory Document**: A PDF version of the professional degree (`degree`) is required for submission.
- Once ready, the professional submits the verification request, changing their `onboarding_status` to `submitted`.

### 2. Admin Review (`/admin/validation/requests`)
- Admins with the `admin_validation` role can list and manage requests.
- Individually approve or reject documents (degree, ID, etc.).
- **Hard Constraint**: The entire request cannot be approved unless at least one `degree` document is marked as `approved`.
- Successful approval transitions the `Professional` model to `status: active` and `onboarding_status: approved`.

### 3. File System Integration
- Environment Variables: `FILES_PATH` (storage root) and `MAX_FILE_SIZE_MB`.
- Soft Delete: Deleted files are moved to a `_deleted/` subdirectory within the storage root, preserving history.

## Common Operations

### Uploading a Document (Frontend)
Use `useApi` with `FormData`. Do not set `Content-Type` manually; the browser will handle `multipart/form-data`.

### Handling Verification State
The `/professionals/me/verification-status` endpoint provides a consolidated view of the professional's current status and associated documents.

## Safety & Anti-Patterns
- **Do NOT** allow profile publication if `onboarding_status` is not `approved`.
- **Do NOT** delete files permanently; always use the `FileStorageService.soft_delete_file` method.
- **NEVER** bypass the PDF requirement for professional degrees.
