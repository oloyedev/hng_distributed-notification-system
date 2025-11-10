# user_service

User service for the HNG Distributed Notification System.

This directory contains the DjangoRestFramework app that manages user accounts, profiles, and related APIs used by the distributed notification system. The service provides user models, serializers, views, and management utilities consumed by the other microservices in the repository.

## What you'll find here

-   `manage.py` — Django management script for running the app, migrations and tests.
-   `requirements.txt` — Python dependencies for this service.
-   `users/` — Django app containing the user models, views, serializers and migrations:
    -   `models.py` — user model(s).
    -   `managers.py` — custom model managers related to users.
    -   `serializers.py` — DRF serializers for user objects.
    -   `views.py` — API views.
    -   `urls.py` — routes for the user APIs.
    -   `tests.py` — unit tests for the app.

## Quick start (local development)

Assumptions:

-   You have Python 3.10+ installed and available as `python` in your shell.
-   You're using the repository-provided `requirements.txt` for dependency installation.

Run the following commands from the `user_service` directory in your terminal (bash):

```bash
# create a virtual environment
python -m venv env

# activate the virtual environment (on Git Bash / WSL use the following)
source env/Scripts/activate

# install dependencies
pip install -r requirements.txt

# apply database migrations
python manage.py migrate

# create a superuser (optional, for admin access)
python manage.py createsuperuser

# run the development server
python manage.py runserver 0.0.0.0:8000
```

Notes:

-   The repository contains a top-level `base/` Django project which this app expects for settings; ensure you're running commands from the `user_service` folder or set `DJANGO_SETTINGS_MODULE` accordingly (e.g. `base.settings`).
-   A `db.sqlite3` file may already exist for convenience in local development.

## Running tests

Run the Django test suite for the users app:

```bash
python manage.py test users
```

## API overview (authoritative)

The following endpoints are defined in `users/urls.py` (paths are relative to the app's mount point).

1.  Create user

    - Method: POST
    - Path: `/` (app root)
    - Request body (JSON):
      {
      "name": "Full Name",
      "email": "user@example.com",
      "password": "plain-text-password",
      "push_token": "optional-push-token",
      "preferences": { "email": true, "push": false }
      }
      Note: `name` maps to the model field `user_name`.
    - Success response: 201
      {
      "message": "User user@example.com created successfully"
      }
    - Validation errors return 400 with serializer error details.

2.  Login (obtain tokens)

    - Method: POST
    - Path: `/login`
    - Request body (JSON):
      { "email": "user@example.com", "password": "secret" }
    - Success response: 200
      {
      "access_tokens": "<access_token>",
      "refresh_token": "<refresh_token>"
      }
      Note: the view returns the keys `access_tokens` (plural) and `refresh_token` (singular).

3.  Update push token (authenticated)

    - Method: PATCH
    - Path: `/update-push-token/`
    - Authentication: required (JWT/access token)
    - Request body (JSON): { "push_token": "new-token-string" }
    - Success response: 200 — returns the updated user representation (see User detail serializer below).
    - Validation: 400 if `push_token` is missing or not a string.

4.  Get current user details (authenticated)

    - Method: GET
    - Path: `/get-details/`
    - Authentication: required
    - Success response: 200
      {
      "email": "user@example.com",
      "name": "Full Name",
      "push_token": "...",
      "preferences": { "email": true, "push": false },
      "created_at": "2025-01-01T12:00:00Z"
      }

5.  Refresh token (SimpleJWT) - Method: POST # user_service

        Lightweight Django app that manages users for the Distributed Notification System.

        Quick start (from `user_service`):

        ```bash
        python -m venv env
        source env/Scripts/activate
        pip install -r requirements.txt
        python manage.py migrate
        python manage.py runserver
        ```

        Key endpoints (paths are relative to where the `users` app is mounted):

        - POST `/` — create user (name, email, password, optional push_token, preferences JSON)
        - POST `/login` — login; returns `access_tokens` and `refresh_token`
        - PATCH `/update-push-token/` — (auth) update current user's push token
        - GET `/get-details/` — (auth) get current user details
        - POST `/refresh-token/` — SimpleJWT token refresh endpoint