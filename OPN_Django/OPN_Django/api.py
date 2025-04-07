from ninja import NinjaAPI
from ninja.security import APIKeyHeader

# Import API endpoints
from OPNSense.api.endpoints.network import router as network_router
from OPNSense.api.endpoints.firewall import router as firewall_router
from OPNSense.api.endpoints.dhcp import router as dhcp_router
from OPNSense.api.endpoints.container import router as container_router
from OPNSense.api.endpoints.onboarding import router as onboarding_router

# API security
class ApiKey(APIKeyHeader):
    param_name = "X-API-Key"
    
    def authenticate(self, request, key):
        # For development, accept any key
        # TODO: Implement proper API key validation
        return key

# Create API instance
api = NinjaAPI(
    title="OPNsense IaC API",
    version="1.0.0",
    description="API for managing OPNsense infrastructure as code",
    auth=ApiKey(),
    urls_namespace="api",
    docs_url="/docs",
)

# Add routers
api.add_router("/network/", network_router)
api.add_router("/firewall/", firewall_router)
api.add_router("/dhcp/", dhcp_router)
api.add_router("/container/", container_router)
api.add_router("/onboarding/", onboarding_router)

# Health check endpoint
@api.get("/health", auth=None)
def health_check(request):
    return {"status": "ok"}
