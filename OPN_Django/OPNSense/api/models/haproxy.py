from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator
import re


class BackendMode(str, Enum):
    """Backend mode for HAProxy."""
    HTTP = "http"
    TCP = "tcp"


class BalanceAlgorithm(str, Enum):
    """Load balancing algorithm for HAProxy."""
    ROUNDROBIN = "roundrobin"
    STATIC_RR = "static-rr"
    LEASTCONN = "leastconn"
    SOURCE = "source"
    URI = "uri"
    URL_PARAM = "url_param"
    HEADER = "hdr"
    RANDOM = "random"


class HAProxyServer(BaseModel):
    """Backend server for HAProxy."""
    name: str = Field(..., description="Server name")
    address: str = Field(..., description="Server address (IP or hostname)")
    port: int = Field(..., description="Server port")
    
    # Optional fields
    check: bool = Field(True, description="Whether to health check this server")
    weight: int = Field(100, description="Server weight for load balancing")
    maxconn: Optional[int] = Field(None, description="Maximum connections")
    
    @validator('port')
    def validate_port(cls, v):
        if v < 1 or v > 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v
    
    @validator('weight')
    def validate_weight(cls, v):
        if v < 0 or v > 256:
            raise ValueError('Weight must be between 0 and 256')
        return v
    
    @validator('maxconn')
    def validate_maxconn(cls, v):
        if v is not None and v < 0:
            raise ValueError('Max connections must be positive')
        return v


class HAProxyBackendBase(BaseModel):
    """Base model for HAProxy backends."""
    name: str = Field(..., description="Backend name")
    mode: BackendMode = Field(BackendMode.HTTP, description="Backend mode")
    balance: BalanceAlgorithm = Field(BalanceAlgorithm.ROUNDROBIN, description="Load balancing algorithm")
    
    # Servers
    servers: List[HAProxyServer] = Field([], description="Backend servers")
    
    # Optional fields
    check_interval: int = Field(2000, description="Health check interval in ms")
    retries: int = Field(3, description="Number of retries for health checks")
    timeout_connect: int = Field(5000, description="Connection timeout in ms")
    timeout_server: int = Field(50000, description="Server response timeout in ms")
    
    @validator('check_interval', 'timeout_connect', 'timeout_server')
    def validate_timeouts(cls, v):
        if v < 0:
            raise ValueError('Timeout values must be positive')
        return v
    
    @validator('retries')
    def validate_retries(cls, v):
        if v < 0:
            raise ValueError('Retries must be positive')
        return v


class HAProxyBackendCreate(HAProxyBackendBase):
    """Model for creating a new HAProxy backend."""
    pass


class HAProxyBackendUpdate(HAProxyBackendBase):
    """Model for updating an existing HAProxy backend."""
    name: Optional[str] = None
    mode: Optional[BackendMode] = None
    balance: Optional[BalanceAlgorithm] = None
    servers: Optional[List[HAProxyServer]] = None
    check_interval: Optional[int] = None
    retries: Optional[int] = None
    timeout_connect: Optional[int] = None
    timeout_server: Optional[int] = None


class HAProxyBackendOut(HAProxyBackendBase):
    """Model for HAProxy backend output."""
    uuid: str = Field(..., description="UUID of the backend")


class HAProxyFrontendBase(BaseModel):
    """Base model for HAProxy frontends."""
    name: str = Field(..., description="Frontend name")
    bind_address: str = Field("0.0.0.0", description="Bind address")
    bind_port: int = Field(..., description="Bind port")
    mode: BackendMode = Field(BackendMode.HTTP, description="Frontend mode")
    default_backend: str = Field(..., description="Default backend name")
    
    # Optional fields
    max_connections: Optional[int] = Field(None, description="Maximum connections")
    timeout_client: int = Field(50000, description="Client timeout in ms")
    enable_ssl: bool = Field(False, description="Enable SSL")
    cert_name: Optional[str] = Field(None, description="SSL certificate name")
    
    @validator('bind_port')
    def validate_port(cls, v):
        if v < 1 or v > 65535:
            raise ValueError('Port must be between 1 and 65535')
        return v
    
    @validator('timeout_client')
    def validate_timeout(cls, v):
        if v < 0:
            raise ValueError('Timeout value must be positive')
        return v
    
    @validator('cert_name')
    def validate_cert(cls, v, values):
        if values.get('enable_ssl') and v is None:
            raise ValueError('Certificate name must be provided when SSL is enabled')
        return v


class HAProxyFrontendCreate(HAProxyFrontendBase):
    """Model for creating a new HAProxy frontend."""
    pass


class HAProxyFrontendUpdate(HAProxyFrontendBase):
    """Model for updating an existing HAProxy frontend."""
    name: Optional[str] = None
    bind_address: Optional[str] = None
    bind_port: Optional[int] = None
    mode: Optional[BackendMode] = None
    default_backend: Optional[str] = None
    max_connections: Optional[int] = None
    timeout_client: Optional[int] = None
    enable_ssl: Optional[bool] = None
    cert_name: Optional[str] = None


class HAProxyFrontendOut(HAProxyFrontendBase):
    """Model for HAProxy frontend output."""
    uuid: str = Field(..., description="UUID of the frontend")


class HAProxyConfigBase(BaseModel):
    """Base model for overall HAProxy configuration."""
    enabled: bool = Field(True, description="Whether HAProxy is enabled")
    
    # Global settings
    max_connections: int = Field(10000, description="Maximum connections")
    timeout_connect: int = Field(5000, description="Connection timeout in ms")
    timeout_client: int = Field(50000, description="Client timeout in ms")
    timeout_server: int = Field(50000, description="Server timeout in ms")
    
    # References to frontends and backends
    frontends: List[str] = Field([], description="List of frontend UUIDs")
    backends: List[str] = Field([], description="List of backend UUIDs")


class HAProxyConfigCreate(HAProxyConfigBase):
    """Model for creating HAProxy configuration."""
    pass


class HAProxyConfigUpdate(HAProxyConfigBase):
    """Model for updating HAProxy configuration."""
    enabled: Optional[bool] = None
    max_connections: Optional[int] = None
    timeout_connect: Optional[int] = None
    timeout_client: Optional[int] = None
    timeout_server: Optional[int] = None
    frontends: Optional[List[str]] = None
    backends: Optional[List[str]] = None


class HAProxyConfigOut(HAProxyConfigBase):
    """Model for HAProxy configuration output."""
    uuid: str = Field(..., description="UUID of the configuration")
    frontends: List[HAProxyFrontendOut] = Field([], description="Frontend configurations")
    backends: List[HAProxyBackendOut] = Field([], description="Backend configurations")
