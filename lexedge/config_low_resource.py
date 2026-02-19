"""
Low-resource configuration settings for lexedge.

This configuration is optimized for machines with limited resources:
- 2-4 GB RAM
- 2-4 CPU cores
- 50-100 concurrent users
"""

import os

# ============================================================================
# RESOURCE LIMITS
# ============================================================================

# WebSocket Connection Limits
MAX_WEBSOCKET_CONNECTIONS = int(os.getenv("MAX_WEBSOCKET_CONNECTIONS", "100"))
MAX_CONNECTIONS_PER_USER = int(os.getenv("MAX_CONNECTIONS_PER_USER", "3"))
WEBSOCKET_HEARTBEAT_INTERVAL = int(os.getenv("WEBSOCKET_HEARTBEAT_INTERVAL", "30"))
WEBSOCKET_CONNECTION_TIMEOUT = int(os.getenv("WEBSOCKET_CONNECTION_TIMEOUT", "300"))

# Redis Configuration (Low Memory)
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
REDIS_POOL_SIZE = int(os.getenv("REDIS_POOL_SIZE", "10"))  # Small pool for low resources
SESSION_TTL_HOURS = int(os.getenv("SESSION_TTL_HOURS", "2"))

# Session Management
MAX_SESSIONS_PER_USER = int(os.getenv("MAX_SESSIONS_PER_USER", "5"))
MAX_MESSAGES_PER_SESSION = int(os.getenv("MAX_MESSAGES_PER_SESSION", "50"))  # Reduced from 100

# Database Settings
USE_REDIS_SESSIONS = os.getenv("USE_REDIS_SESSIONS", "true").lower() == "true"
ENABLE_SESSION_FALLBACK = os.getenv("ENABLE_SESSION_FALLBACK", "true").lower() == "true"

# ============================================================================
# PERFORMANCE OPTIMIZATION
# ============================================================================

# Agent Processing
AGENT_TIMEOUT_SECONDS = int(os.getenv("AGENT_TIMEOUT_SECONDS", "30"))
ENABLE_AGENT_CACHING = os.getenv("ENABLE_AGENT_CACHING", "true").lower() == "true"

# Message Compression
ENABLE_WEBSOCKET_COMPRESSION = os.getenv("ENABLE_WEBSOCKET_COMPRESSION", "true").lower() == "true"

# Rate Limiting
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
RATE_LIMIT_PER_HOUR = int(os.getenv("RATE_LIMIT_PER_HOUR", "500"))

# ============================================================================
# MONITORING
# ============================================================================

# Resource Monitoring
ENABLE_RESOURCE_MONITORING = os.getenv("ENABLE_RESOURCE_MONITORING", "true").lower() == "true"
RESOURCE_CHECK_INTERVAL = int(os.getenv("RESOURCE_CHECK_INTERVAL", "60"))  # seconds

# Memory Thresholds
MEMORY_WARNING_THRESHOLD = int(os.getenv("MEMORY_WARNING_THRESHOLD", "80"))  # percent
MEMORY_CRITICAL_THRESHOLD = int(os.getenv("MEMORY_CRITICAL_THRESHOLD", "90"))  # percent

# CPU Thresholds
CPU_WARNING_THRESHOLD = int(os.getenv("CPU_WARNING_THRESHOLD", "80"))  # percent
CPU_CRITICAL_THRESHOLD = int(os.getenv("CPU_CRITICAL_THRESHOLD", "90"))  # percent

# ============================================================================
# CLEANUP & MAINTENANCE
# ============================================================================

# Automatic Cleanup
ENABLE_AUTO_CLEANUP = os.getenv("ENABLE_AUTO_CLEANUP", "true").lower() == "true"
CLEANUP_INTERVAL_SECONDS = int(os.getenv("CLEANUP_INTERVAL_SECONDS", "300"))  # 5 minutes

# Session Cleanup
CLEANUP_EXPIRED_SESSIONS = os.getenv("CLEANUP_EXPIRED_SESSIONS", "true").lower() == "true"
CLEANUP_STALE_CONNECTIONS = os.getenv("CLEANUP_STALE_CONNECTIONS", "true").lower() == "true"

# ============================================================================
# FEATURE FLAGS
# ============================================================================

# Optional Features (disable to save resources)
ENABLE_DETAILED_LOGGING = os.getenv("ENABLE_DETAILED_LOGGING", "false").lower() == "true"
ENABLE_METRICS_EXPORT = os.getenv("ENABLE_METRICS_EXPORT", "false").lower() == "true"
ENABLE_DEBUG_MODE = os.getenv("ENABLE_DEBUG_MODE", "false").lower() == "true"

# ============================================================================
# UVICORN SERVER SETTINGS (for low resources)
# ============================================================================

UVICORN_CONFIG = {
    "host": "0.0.0.0",
    "port": 3334,
    "workers": 1,  # Single worker for low resources
    "limit_concurrency": MAX_WEBSOCKET_CONNECTIONS,
    "timeout_keep_alive": 30,
    "timeout_graceful_shutdown": 10,
    "log_level": "info",
    "access_log": not ENABLE_DETAILED_LOGGING,  # Disable access log to save resources
}

# ============================================================================
# REDIS CONFIGURATION FILE TEMPLATE
# ============================================================================

REDIS_CONFIG_TEMPLATE = """
# Redis configuration for low-resource machines
# Save this as redis-low-memory.conf and run: redis-server redis-low-memory.conf

# Memory Management
maxmemory 256mb
maxmemory-policy allkeys-lru

# Persistence (disabled for lower I/O)
save ""
appendonly no

# Network
tcp-backlog 128
timeout 300

# Performance
databases 2
tcp-keepalive 60

# Logging
loglevel notice
"""

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_resource_config() -> dict:
    """Get current resource configuration"""
    return {
        "websocket": {
            "max_total_connections": MAX_WEBSOCKET_CONNECTIONS,
            "max_connections_per_user": MAX_CONNECTIONS_PER_USER,
            "heartbeat_interval": WEBSOCKET_HEARTBEAT_INTERVAL,
            "connection_timeout": WEBSOCKET_CONNECTION_TIMEOUT,
        },
        "redis": {
            "url": REDIS_URL,
            "pool_size": REDIS_POOL_SIZE,
            "session_ttl_hours": SESSION_TTL_HOURS,
        },
        "sessions": {
            "max_per_user": MAX_SESSIONS_PER_USER,
            "max_messages": MAX_MESSAGES_PER_SESSION,
            "use_redis": USE_REDIS_SESSIONS,
            "enable_fallback": ENABLE_SESSION_FALLBACK,
        },
        "performance": {
            "agent_timeout": AGENT_TIMEOUT_SECONDS,
            "enable_caching": ENABLE_AGENT_CACHING,
            "enable_compression": ENABLE_WEBSOCKET_COMPRESSION,
        },
        "rate_limiting": {
            "per_minute": RATE_LIMIT_PER_MINUTE,
            "per_hour": RATE_LIMIT_PER_HOUR,
        },
        "monitoring": {
            "enabled": ENABLE_RESOURCE_MONITORING,
            "check_interval": RESOURCE_CHECK_INTERVAL,
            "memory_warning": MEMORY_WARNING_THRESHOLD,
            "cpu_warning": CPU_WARNING_THRESHOLD,
        },
        "cleanup": {
            "enabled": ENABLE_AUTO_CLEANUP,
            "interval": CLEANUP_INTERVAL_SECONDS,
            "cleanup_sessions": CLEANUP_EXPIRED_SESSIONS,
            "cleanup_connections": CLEANUP_STALE_CONNECTIONS,
        }
    }


def print_config():
    """Print current configuration"""
    import json
    config = get_resource_config()
    print("=" * 60)
    print("LOW-RESOURCE CONFIGURATION")
    print("=" * 60)
    print(json.dumps(config, indent=2))
    print("=" * 60)


def generate_redis_config_file(output_path: str = "redis-low-memory.conf"):
    """Generate Redis configuration file for low resources"""
    with open(output_path, "w") as f:
        f.write(REDIS_CONFIG_TEMPLATE)
    print(f"✅ Redis config generated: {output_path}")
    print(f"   Run with: redis-server {output_path}")


if __name__ == "__main__":
    print_config()
    generate_redis_config_file()
