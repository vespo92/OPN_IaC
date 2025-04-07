from django.contrib import admin
from .models import (
    OPNsenseServer,
    NetworkInterface,
    VLAN,
    FirewallRule,
    PortForward,
    DHCPServer,
    DHCPStaticMapping,
    Container,
    HAProxyBackend,
    HAProxyFrontend,
    DeploymentLog
)


@admin.register(OPNsenseServer)
class OPNsenseServerAdmin(admin.ModelAdmin):
    list_display = ('name', 'hostname', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'hostname')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(NetworkInterface)
class NetworkInterfaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'server', 'if_name', 'ipaddr', 'enabled', 'updated_at')
    list_filter = ('enabled', 'server')
    search_fields = ('name', 'if_name', 'ipaddr')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(VLAN)
class VLANAdmin(admin.ModelAdmin):
    list_display = ('parent_if', 'vlan_tag', 'server', 'description', 'vlanif', 'updated_at')
    list_filter = ('server',)
    search_fields = ('parent_if', 'vlanif', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(FirewallRule)
class FirewallRuleAdmin(admin.ModelAdmin):
    list_display = ('action', 'protocol', 'server', 'interface', 'src_address', 'dst_address', 'enabled', 'updated_at')
    list_filter = ('action', 'protocol', 'enabled', 'server')
    search_fields = ('description', 'src_address', 'dst_address')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(PortForward)
class PortForwardAdmin(admin.ModelAdmin):
    list_display = ('protocol', 'src_port', 'dst_ip', 'dst_port', 'server', 'enabled', 'updated_at')
    list_filter = ('protocol', 'enabled', 'server')
    search_fields = ('description', 'src_port', 'dst_ip', 'dst_port')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(DHCPServer)
class DHCPServerAdmin(admin.ModelAdmin):
    list_display = ('interface', 'server', 'enabled', 'range_from', 'range_to', 'updated_at')
    list_filter = ('enabled', 'server')
    search_fields = ('interface', 'range_from', 'range_to')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(DHCPStaticMapping)
class DHCPStaticMappingAdmin(admin.ModelAdmin):
    list_display = ('mac', 'ipaddr', 'hostname', 'dhcp_server', 'updated_at')
    list_filter = ('dhcp_server',)
    search_fields = ('mac', 'ipaddr', 'hostname', 'description')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(Container)
class ContainerAdmin(admin.ModelAdmin):
    list_display = ('name', 'image', 'status', 'ip_address', 'vlan_id', 'updated_at')
    list_filter = ('status', 'vlan_id', 'allow_internet')
    search_fields = ('name', 'image', 'ip_address')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(HAProxyBackend)
class HAProxyBackendAdmin(admin.ModelAdmin):
    list_display = ('name', 'server', 'mode', 'balance', 'updated_at')
    list_filter = ('mode', 'server')
    search_fields = ('name',)
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(HAProxyFrontend)
class HAProxyFrontendAdmin(admin.ModelAdmin):
    list_display = ('name', 'server', 'bind_address', 'bind_port', 'mode', 'default_backend', 'updated_at')
    list_filter = ('mode', 'enable_ssl', 'server')
    search_fields = ('name', 'bind_address', 'default_backend')
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(DeploymentLog)
class DeploymentLogAdmin(admin.ModelAdmin):
    list_display = ('container', 'action', 'status', 'created_at')
    list_filter = ('action', 'status')
    search_fields = ('container__name', 'message')
    readonly_fields = ('id', 'created_at', 'updated_at', 'container', 'action', 'status', 'message', 'details')
