#!/bin/bash
set -e

echo "=== Squid SSL Bump Startup Script ==="
echo "Starting at: $(date)"

echo "Checking CA certificate..."
if [ ! -f /etc/squid/squidCA.pem ] || [ ! -f /etc/squid/squidCA.key ]; then
    echo "ERROR: CA certificate or key not found!"
    echo "Make sure to mount valid certificate files to /etc/squid/squidCA.pem and /etc/squid/squidCA.key"
    exit 1
fi

echo "Certificate files found:"
ls -la /etc/squid/squidCA.*

echo "Checking certificate permissions..."
# Check if filesystem is read-only before attempting to chmod
if touch /etc/squid/permissions_test 2>/dev/null; then
    rm /etc/squid/permissions_test
    chmod 400 /etc/squid/squidCA.key
    chmod 444 /etc/squid/squidCA.pem
    echo "Certificate permissions updated."
else
    echo "Filesystem is read-only. Skipping permission changes."
    # If files are mounted read-only, we need to copy them to a writable location
    if [ ! -d /tmp/squid_certs ]; then
        mkdir -p /tmp/squid_certs
    fi
    cp /etc/squid/squidCA.key /tmp/squid_certs/
    cp /etc/squid/squidCA.pem /tmp/squid_certs/
    chmod 400 /tmp/squid_certs/squidCA.key
    chmod 444 /tmp/squid_certs/squidCA.pem

    # Update squid.conf to use the copied certificates
    sed -i 's|cert=/etc/squid/squidCA.pem|cert=/tmp/squid_certs/squidCA.pem|g' /etc/squid/squid.conf
    sed -i 's|key=/etc/squid/squidCA.key|key=/tmp/squid_certs/squidCA.key|g' /etc/squid/squid.conf
    echo "Certificates copied to writable location and squid.conf updated."
fi

# Check if we're using SSL configuration
if grep -q "ssl_bump\|sslcrtd_program" /etc/squid/squid.conf; then
    echo "SSL configuration detected, initializing SSL DB..."
    
    # Use only the main SSL DB location with tmpfs mount
    SSL_DB_PATH="/var/lib/ssl_db"
    echo "Initializing SSL DB at: $SSL_DB_PATH"

    # Print detailed debug info
    echo "SSL DB directory details:"
    ls -la $SSL_DB_PATH
    echo "Proxy user information:"
    id proxy
    echo "Directory permissions:"
    stat $SSL_DB_PATH

    echo "Setting SSL DB directory permissions..."
    # Ensure directory has correct permissions (should already be set by tmpfs mount)
    chown -R proxy:proxy $SSL_DB_PATH
    chmod -R 750 $SSL_DB_PATH

    # Test if proxy user can write to the directory
    if su -s /bin/sh proxy -c "touch $SSL_DB_PATH/test_write"; then
        echo "SSL DB directory is writable by the proxy user"
        rm $SSL_DB_PATH/test_write

        # Try initializing SSL DB - the tool works silently, so we check for file creation
        echo "Initializing SSL certificate database..."
        echo "Running: /usr/lib/squid/security_file_certgen -c -s $SSL_DB_PATH -M 16MB"
        
        # Run the tool - it works silently, so we check the result by looking for created files
        if /usr/lib/squid/security_file_certgen -c -s $SSL_DB_PATH -M 16MB; then
            echo "security_file_certgen tool completed"
            
            # Check if the SSL DB was actually created by looking for expected files
            if [ -d "$SSL_DB_PATH/certs" ] && [ -f "$SSL_DB_PATH/index.txt" ] && [ -f "$SSL_DB_PATH/size" ]; then
                echo "Successfully initialized SSL DB"
                echo "SSL DB contents:"
                ls -la $SSL_DB_PATH
                echo "SSL DB certs directory:"
                ls -la $SSL_DB_PATH/certs
            else
                echo "WARNING: SSL DB directory structure incomplete after initialization"
                echo "Expected files not found. SSL bumping may not work properly."
            fi
        else
            echo "ERROR: security_file_certgen tool failed with exit code $?"
            
            # Get more details about the SSL DB directory
            echo "Checking filesystem type:"
            df -Th $SSL_DB_PATH
            echo "Mount information:"
            mount | grep -E "ssl_db|tmpfs"
            
            # Try alternative initialization method
            echo "Trying alternative SSL DB initialization..."
            if su -s /bin/sh proxy -c "/usr/lib/squid/security_file_certgen -c -s $SSL_DB_PATH -M 16MB"; then
                echo "Alternative initialization successful"
            else
                echo "Alternative initialization also failed"
                echo "WARNING: SSL bumping may not work properly"
            fi
        fi
    else
        echo "ERROR: SSL DB directory is NOT writable by the proxy user"
        echo "Checking filesystem type and mount options:"
        df -Th $SSL_DB_PATH
        mount | grep -E "ssl_db|tmpfs"
        echo "WARNING: SSL bumping may not work properly"
    fi
else
    echo "Non-SSL configuration detected, skipping SSL DB initialization"
fi

# Clean up any stale PID files and processes
echo "Cleaning up stale PID files and processes..."
rm -f /var/run/squid.pid
pkill -f "squid" || true
sleep 2

# Create cache directories
echo "Creating cache directories"
/usr/sbin/squid -z

# Wait a moment for any background processes to settle
sleep 3

echo "Starting Squid in foreground mode..."
exec /usr/sbin/squid -N -d 2 -f /etc/squid/squid.conf


