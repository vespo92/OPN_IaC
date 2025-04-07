from django.db import models
import uuid
import json


class BaseModel(models.Model):
    """Base model with common fields."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class OPNsenseServer(BaseModel):
    """Model for OPNsense server configuration."""
    
    name = models.CharField(max_length=100, unique=True)
    hostname = models.CharField(max_length=255)
    api_key = models.CharField(max_length=255)
    api_secret = models.CharField(max_length=255)
    verify_ssl = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "OPNsense Server"
        verbose_name_plural = "OPNsense Servers"


class NetworkInterface(BaseModel):
    """Model for network interfaces."""
    
    server = models.ForeignKey(OPNsenseServer, on_delete=models.CASCADE, related_name='interfaces')
    name = models.CharField(max_length=50)
    if_name = models.CharField(max_length=50)
    description = models.CharField(max_length=255, blank=True)
    ipaddr = models.CharField(max_length=50, default='dhcp')
    subnet = models.IntegerField(null=True, blank=True)
    enabled = models.BooleanField(default=True)
    gateway = models.CharField(max_length=50, blank=True)
    spoofmac = models.CharField(max_length=50, blank=True)
    mtu = models.IntegerField(null=True, blank=True)
    media = models.CharField(max_length=50, blank=True)
    mediaopt = models.CharField(max_length=50, blank=True)
    opnsense_uuid = models.CharField(max_length=36, blank=True)
    
    def __str__(self):
        return f"{self.server.name} - {self.name}"
    
    class Meta:
        verbose_name = "Network Interface"
        verbose_name_plural = "Network Interfaces"
        unique_together = ('server', 'name')


class VLAN(BaseModel):
    """Model for VLANs."""
    
    server = models.ForeignKey(OPNsenseServer, on_delete=models.CASCADE, related_name='vlans')
    parent_if = models.CharField(max_length=50)
    vlan_tag = models.IntegerField()
    description = models.CharField(max_length=255, blank=True)
    pcp = models.IntegerField(default=0)
    vlanif = models.CharField(max_length=50, blank=True)
    opnsense_uuid = models.CharField(max_length=36, blank=True)
    
    def __str__(self):
        return f"{self.server.name} - VLAN {self.vlan_tag} on {self.parent_if}"
    
    class Meta:
        verbose_name = "VLAN"
        verbose_name_plural = "VLANs"
        unique_together = ('server', 'parent_if', 'vlan_tag')


class FirewallRule(BaseModel):
    """Model for firewall rules."""
    
    server = models.ForeignKey(OPNsenseServer, on_delete=models.CASCADE, related_name='firewall_rules')
    interface = models.CharField(max_length=50)
    protocol = models.CharField(max_length=10, default='any')
    src_address = models.CharField(max_length=50, blank=True)
    src_port = models.CharField(max_length=50, blank=True)
    dst_address = models.CharField(max_length=50, blank=True)
    dst_port = models.CharField(max_length=50, blank=True)
    action = models.CharField(max_length=10, default='pass')
    description = models.CharField(max_length=255, blank=True)
    enabled = models.BooleanField(default=True)
    direction = models.CharField(max_length=10, default='in')
    ipprotocol = models.CharField(max_length=10, default='inet')
    opnsense_uuid = models.CharField(max_length=36, blank=True)
    
    def __str__(self):
        return f"{self.server.name} - {self.action} {self.protocol} to {self.dst_address}"
    
    class Meta:
        verbose_name = "Firewall Rule"
        verbose_name_plural = "Firewall Rules"


class PortForward(BaseModel):
    """Model for port forwarding rules."""
    
    server = models.ForeignKey(OPNsenseServer, on_delete=models.CASCADE, related_name='port_forwards')
    interface = models.CharField(max_length=50)
    protocol = models.CharField(max_length=10, default='tcp')
    src_port = models.CharField(max_length=50)
    dst_ip = models.CharField(max_length=50)
    dst_port = models.CharField(max_length=50)
    description = models.CharField(max_length=255, blank=True)
    src_ip = models.CharField(max_length=50, blank=True)
    enabled = models.BooleanField(default=True)
    opnsense_uuid = models.CharField(max_length=36, blank=True)
    
    def __str__(self):
        return f"{self.server.name} - {self.protocol}/{self.src_port} to {self.dst_ip}:{self.dst_port}"
    
    class Meta:
        verbose_name = "Port Forward"
        verbose_name_plural = "Port Forwards"


class DHCPServer(BaseModel):
    """Model for DHCP server configuration."""
    
    server = models.ForeignKey(OPNsenseServer, on_delete=models.CASCADE, related_name='dhcp_servers')
    interface = models.CharField(max_length=50)
    enabled = models.BooleanField(default=True)
    range_from = models.CharField(max_length=50, blank=True)
    range_to = models.CharField(max_length=50, blank=True)
    gateway = models.CharField(max_length=50, blank=True)
    dnsserver = models.CharField(max_length=50, blank=True)
    domain = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return f"{self.server.name} - DHCP on {self.interface}"
    
    class Meta:
        verbose_name = "DHCP Server"
        verbose_name_plural = "DHCP Servers"
        unique_together = ('server', 'interface')


class DHCPStaticMapping(BaseModel):
    """Model for DHCP static mappings."""
    
    dhcp_server = models.ForeignKey(DHCPServer, on_delete=models.CASCADE, related_name='static_mappings')
    mac = models.CharField(max_length=17)
    ipaddr = models.CharField(max_length=50)
    hostname = models.CharField(max_length=50)
    description = models.CharField(max_length=255, blank=True)
    winsserver = models.CharField(max_length=50, blank=True)
    dnsserver = models.CharField(max_length=50, blank=True)
    ntpserver = models.CharField(max_length=50, blank=True)
    opnsense_uuid = models.CharField(max_length=36, blank=True)
    
    def __str__(self):
        return f"{self.dhcp_server.server.name} - {self.mac} to {self.ipaddr}"
    
    class Meta:
        verbose_name = "DHCP Static Mapping"
        verbose_name_plural = "DHCP Static Mappings"
        unique_together = ('dhcp_server', 'mac')


class Container(BaseModel):
    """Model for containers."""
    
    name = models.CharField(max_length=100, unique=True)
    image = models.CharField(max_length=255)
    docker_id = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=20, default='created')
    vlan_id = models.IntegerField()
    ip_address = models.CharField(max_length=50)
    mac_address = models.CharField(max_length=17)
    parent_interface = models.CharField(max_length=50, default='igc2')
    allow_internet = models.BooleanField(default=True)
    ports = models.JSONField(default=list)
    environment = models.JSONField(default=dict)
    volumes = models.JSONField(default=dict)
    restart_policy = models.CharField(max_length=20, default='unless-stopped')
    
    def __str__(self):
        return self.name
    
    def get_ports(self):
        return self.ports
    
    def get_environment(self):
        return self.environment
    
    def get_volumes(self):
        return self.volumes
    
    class Meta:
        verbose_name = "Container"
        verbose_name_plural = "Containers"


class HAProxyBackend(BaseModel):
    """Model for HAProxy backends."""
    
    server = models.ForeignKey(OPNsenseServer, on_delete=models.CASCADE, related_name='haproxy_backends')
    name = models.CharField(max_length=100)
    mode = models.CharField(max_length=10, default='http')
    balance = models.CharField(max_length=20, default='roundrobin')
    servers = models.JSONField(default=list)
    check_interval = models.IntegerField(default=2000)
    retries = models.IntegerField(default=3)
    timeout_connect = models.IntegerField(default=5000)
    timeout_server = models.IntegerField(default=50000)
    opnsense_uuid = models.CharField(max_length=36, blank=True)
    
    def __str__(self):
        return f"{self.server.name} - HAProxy Backend {self.name}"
    
    class Meta:
        verbose_name = "HAProxy Backend"
        verbose_name_plural = "HAProxy Backends"
        unique_together = ('server', 'name')


class HAProxyFrontend(BaseModel):
    """Model for HAProxy frontends."""
    
    server = models.ForeignKey(OPNsenseServer, on_delete=models.CASCADE, related_name='haproxy_frontends')
    name = models.CharField(max_length=100)
    bind_address = models.CharField(max_length=50, default='0.0.0.0')
    bind_port = models.IntegerField()
    mode = models.CharField(max_length=10, default='http')
    default_backend = models.CharField(max_length=100)
    max_connections = models.IntegerField(null=True, blank=True)
    timeout_client = models.IntegerField(default=50000)
    enable_ssl = models.BooleanField(default=False)
    cert_name = models.CharField(max_length=100, blank=True, null=True)
    opnsense_uuid = models.CharField(max_length=36, blank=True)
    
    def __str__(self):
        return f"{self.server.name} - HAProxy Frontend {self.name}"
    
    class Meta:
        verbose_name = "HAProxy Frontend"
        verbose_name_plural = "HAProxy Frontends"
        unique_together = ('server', 'name')


class DeploymentLog(BaseModel):
    """Model for deployment logs."""
    
    container = models.ForeignKey(Container, on_delete=models.CASCADE, related_name='deployment_logs', null=True, blank=True)
    action = models.CharField(max_length=20)
    status = models.CharField(max_length=20)
    message = models.TextField(blank=True)
    details = models.JSONField(default=dict)
    
    def __str__(self):
        return f"{self.container.name if self.container else 'Unknown'} - {self.action} - {self.status}"
    
    class Meta:
        verbose_name = "Deployment Log"
        verbose_name_plural = "Deployment Logs"
