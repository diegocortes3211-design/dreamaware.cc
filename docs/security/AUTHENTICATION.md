# Authentication and Authorization Flow

This document details the JWT-based authentication and authorization flow for the Xikizpedia API.

## Overview

The API uses JSON Web Tokens (JWTs) to authenticate users and authorize access to protected endpoints. The flow is as follows:

1.  A client sends user credentials (username and password) to the `/auth/login` endpoint.
2.  The server validates the credentials.
3.  If valid, the server generates a signed JWT (access token) and returns it to the client.
4.  The client stores this token securely.
5.  For all subsequent requests to protected endpoints, the client must include the access token in the `Authorization` header using the `Bearer` scheme.
6.  The server's middleware intercepts each request, validates the token, and grants access if the token is valid.

## Token Structure and Policy

*   **Algorithm**: `RS256` (RSA Signature with SHA-256). This is an asymmetric algorithm, meaning a private key is used to sign the tokens and a public key is used to verify them.
*   **Payload Claims**:
    *   `sub` (Subject): The username of the user.
    *   `exp` (Expiration Time): The timestamp indicating when the token will expire.
*   **Expiration**: Access tokens are short-lived. They are configured to expire **30 minutes** after being issued. (Note: A refresh token flow is not yet implemented in this version).

## How to Authenticate and Make a Request

Below are examples of how to interact with the API's authentication system.

### 1. Log in to get an Access Token

First, make a `POST` request to the `/auth/login` endpoint with the user's credentials in a form-data body.

**Request:**

```bash
curl -X POST "http://127.0.0.1:8000/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=testuser&password=password123"
```

**Successful Response (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTcxNjY4ODAwMH0.example_signature",
  "token_type": "bearer"
}
```

### 2. Make a Request to a Protected Endpoint

Once you have the `access_token`, include it in the `Authorization` header of your requests to protected endpoints, such as `/leaderboard/`.

**Request:**

```bash
curl -X GET "http://127.0.0.1:8000/leaderboard/" \
     -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciIsImV4cCI6MTcxNjY4ODAwMH0.example_signature"
```

**Successful Response (200 OK):**

The API will return the data for the requested endpoint.

**Failed Response (401 Unauthorized):**

If the token is missing, invalid, or expired, the API will return a `401 Unauthorized` error.

```json
{
  "detail": "Invalid authentication credentials"
}
```