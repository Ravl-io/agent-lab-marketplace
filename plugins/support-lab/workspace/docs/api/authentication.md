# Authentication

API clients authenticate with a client credential (`client_id` / secret) issued by a tenant admin. Tokens expire after 60 minutes. Each request is logged with its `client_id`.
