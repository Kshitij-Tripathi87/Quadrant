# DocuSign OAuth 2.0: JWT Grant Authentication Architecture

DocuSign supports OAuth 2.0 JSON Web Token (JWT) Grant for server-to-server and background service integrations. With JWT Grant, backend microservices authenticate autonomously on behalf of a system user without interactive browser sign-in.

## 1. Prerequisites and Key Configuration

To authenticate via JWT Grant, generate credentials in the DocuSign Developer Admin Console:
1. **Integration Key (Client ID)**: Unique GUID representing your application.
2. **User ID (Impersonated User GUID)**: GUID of the account user on whose behalf actions are taken.
3. **RSA Private Key**: 2048-bit RSA private key stored securely in your secrets manager.
4. **OAuth Scopes**: Must include `signature` (for eSignature API) and `impersonation` (delegated execution).
5. **Admin Consent**: The user or organization admin must grant one-time consent via browser URL:
   `https://account-d.docusign.com/oauth/auth?response_type=code&scope=signature%20impersonation&client_id={INTEGRATION_KEY}&redirect_uri={CALLBACK_URL}`

---

## 2. Python Implementation: Requesting JWT Token

Use `ApiClient.request_jwt_user_token` to exchange an RSA-signed assertion for a short-lived Bearer access token (valid for 3600 seconds).

```python
import os
from docusign_esign import ApiClient

def get_docusign_jwt_client(
    integration_key: str,
    user_id: str,
    rsa_private_key_path: str,
    oauth_host: str = "account-d.docusign.com",
) -> ApiClient:
    """
    Authenticates via DocuSign JWT Grant and initializes an ApiClient
    with valid Bearer credentials and base URI discovery.
    """
    with open(rsa_private_key_path, "rb") as key_file:
        private_key_bytes = key_file.read()

    api_client = ApiClient()
    api_client.set_oauth_host(oauth_host)

    # Request Access Token (1 hour validity)
    token_response = api_client.request_jwt_user_token(
        client_id=integration_key,
        user_id=user_id,
        oauth_host_name=oauth_host,
        private_key_bytes=private_key_bytes,
        expires_in=3600,
        scopes=["signature", "impersonation"],
    )

    access_token = token_response.access_token

    # Discover User's Default Account ID and REST Base URI
    user_info = api_client.get_user_info(access_token)
    default_account = next(
        acc for acc in user_info.accounts if acc.is_default == "true"
    )

    api_client.host = f"{default_account.base_uri}/restapi"
    api_client.set_default_header("Authorization", f"Bearer {access_token}")

    return api_client
```

---

## 3. Token Lifecycle & Cache Renewal

- **Token Expiry**: DocuSign JWT tokens expire after 1 hour (3600s).
- **Proactive Renewal**: Production applications must cache the access token in Redis or memory and refresh it when fewer than 5 minutes remain before expiry.
- **Error Handling**: If consent has not been granted, the API throws `consent_required`. Your application should catch this and provide the administrative consent URL.
