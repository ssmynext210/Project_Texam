from app.database import Tenant
import uuid

defaultDomain = "default"

DefaultConfigTenant = Tenant(
    id=uuid.uuid4(),
    name="Default Tenant",
    domain=defaultDomain,
    provider="default",
    client_id="ac0yz4hyyfr2ul6hcjirl",
    client_secret="G5ZyJol1FnwqdNnElXTB7vbNpWSTGjt7",
    auth_url="https://logto.mytechcto.com/oidc/auth",
    token_url="https://logto.mytechcto.com/oidc/token",
    userinfo_url="https://logto.mytechcto.com/oidc/me"
)