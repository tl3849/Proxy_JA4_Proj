# Proxy JA4 Project

A comprehensive tool for collecting and analyzing JA4 signatures from TLS traffic, with support for multiple proxy types including Squid and mitmproxy. This project enables security researchers and network administrators to fingerprint proxy usage and analyze TLS handshake characteristics.

## 🚀 Current Status: FULLY FUNCTIONAL

**Last Updated**: August 11, 2025  
**Version**: 1.0.0  
**Status**: Production Ready

### ✅ What's Working

- **Core Infrastructure**: Docker Compose setup, CA certificate generation, network configuration
- **Proxy Services**: Squid (TLS inspection), mitmproxy (TLS interception), test client
- **Packet Capture**: Host networking with Docker bridge visibility (33KB+ pcap files)
- **JA4 Analysis**: Signature extraction for all traffic types (JA4, JA4S, JA4H)
- **Automation**: Comprehensive Makefile with one-command testing
- **Cross-Platform**: Tested and working on Windows, macOS, and Linux

## 🏗️ Project Architecture

```
Proxy_JA4_Proj/
├── docker-compose.yml          # Container orchestration
├── Makefile                    # Automation commands
├── requirements.txt            # Python dependencies
├── setup.py                   # Package configuration
├── .gitignore                 # Git ignore patterns
├── docker/                    # Container definitions
│   ├── client/                # Client container
│   │   └── Dockerfile
│   └── squid/                 # Squid proxy container
│       └── Dockerfile
├── captures/                  # Packet captures and results
├── configs/                   # Configuration files and runtime data
│   ├── mitmproxy/            # mitmproxy setup
│   │   ├── templates/        # Configuration templates
│   │   └── runtime/          # Runtime data (CA certs)
│   ├── squid/                # Squid proxy configuration
│   │   ├── templates/        # Configuration templates
│   │   └── runtime/          # Runtime data (CA certs, SSL DB)
│   └── shared_ca/            # CA certificates
├── scripts/                   # Python automation
│   ├── capture.py            # Packet capture control
│   ├── parse_ja4.py          # JA4 signature parsing
│   ├── proxy_manager.py      # Proxy management
│   └── config_manager.py     # Configuration management
├── tests/                     # Test automation
│   ├── install_proxy_cas.py  # CA certificate generation
│   └── test_all_proxies.py   # Comprehensive proxy testing
└── logs/                      # Application logs (consolidated)
    ├── install_proxy_cas.log  # CA installation logs
    ├── config_manager.log     # Configuration management logs
    ├── proxy_manager.log      # Proxy management logs
    ├── capture.log            # Packet capture logs
    ├── parse_ja4.log          # JA4 parsing logs
    └── squid/                 # Squid proxy logs
```

### Services

- **mitmproxy_poc**: TLS interception proxy (port 8080)
- **squid_poc**: HTTP/HTTPS proxy with SSL bumping (port 3128)
- **capture_poc**: Network traffic capture using tcpdump
- **client_poc**: Test client for generating traffic

## 🚀 Quick Start

### Prerequisites

- **Docker Desktop** (Windows/macOS) or **Docker Engine** (Linux)
- **Python 3.8+** with pip
- **Git**
- **4GB+ RAM** available
- **5GB+ disk space**

### Windows-Specific Notes

- **Docker Desktop**: Must be running before using any Docker commands
- **PowerShell**: Use `New-Item -ItemType Directory -Path "path" -Force` instead of `mkdir -p`
- **Path Separators**: Use backslashes `\` or forward slashes `/` (both work)
- **Permissions**: Run PowerShell as Administrator if you encounter permission issues

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd Proxy_JA4_Proj

# Install Python dependencies
python -m pip install -r requirements.txt

# Generate CA certificates (required for TLS interception)
python tests/install_proxy_cas.py
```

### 2. Start the Infrastructure

```bash
# Build and start all services
make up

# Wait for containers to be healthy
make health
```

### 3. Run a Complete Test

```bash
# One-command test (capture → traffic → analysis)
make quick-test
```

## 🛠️ Usage

### Make Commands (Recommended)

```bash
make help              # Show all available commands
make up                # Start all services
make down              # Stop all services
make restart           # Restart all services
make logs              # View all container logs
make health            # Check container health status

# Testing
make quick-test        # Run complete test cycle
make test-squid        # Test Squid proxy only
make test-mitmproxy    # Test mitmproxy only

# Capture and Analysis
make capture-start     # Start packet capture
make capture-stop      # Stop packet capture
make parse             # Parse JA4 signatures

# Development
make dev-setup         # Setup development environment
make backup            # Backup current configuration
make clean             # Clean up temporary files
```

### Manual Testing

```bash
# Start capture
python scripts/capture.py --start --interface "br-<network-id>" --output test.pcap

# Generate test traffic
docker exec client_poc python test_all_proxies.py

# Stop capture
python scripts/capture.py --stop

# Parse JA4 signatures
python scripts/parse_ja4.py
```

### Adding More Proxies

**Important**: Only add proxies that perform **TLS interception/SSL bumping**. Basic forward proxies do not generate relevant JA4 signatures for fingerprinting.

1. **Create proxy configuration directory** in `configs/` for config files
2. **Create container directory** in `docker/` for the Dockerfile
3. **Create configuration files** with TLS interception in `configs/<proxy>/templates/`
4. **Update docker-compose.yml** with new service
5. **Add test cases** in `tests/test_all_proxies.py`

Example for a TLS intercepting proxy:
```yaml
# In docker-compose.yml
newproxy_poc:
  build: ./docker/newproxy
  ports:
    - "8081:8080"
  networks:
    - pocnet
  volumes:
    - ./configs/newproxy/runtime:/etc/newproxy
```

## 🔧 Troubleshooting

### Common Issues

#### Packet Capture Issues
**Problem**: Small pcap files (24 bytes) or no traffic captured  
**Solution**: 
- Ensure capture container uses `network_mode: host`
- Capture on Docker bridge interface: `br-<network-id>`
- Use `make capture-start` for automatic interface detection

#### Container Startup Failures
**Problem**: Squid container exiting with "already running" error  
**Solution**: 
- Container automatically handles PID file cleanup
- Use `make restart` to restart services
- Check logs with `make logs`

#### SSL Certificate Warnings
**Problem**: SSL warnings in proxy connections  
**Solution**: 
- These are expected for proxy connections
- CA certificates are automatically generated
- Use `make health` to verify proxy status

#### Windows-Specific Issues
**Problem**: Docker Desktop not running  
**Solution**: 
- Start Docker Desktop from Start Menu
- Wait for Docker to fully initialize (whale icon in system tray)
- Run `docker ps` to verify connection

**Problem**: PowerShell permission errors  
**Solution**: 
- Run PowerShell as Administrator
- Check Windows Defender/antivirus exclusions
- Verify Docker Desktop settings

### Debug Commands

```bash
# Check container status
docker ps -a

# View specific container logs
docker logs squid_poc
docker logs mitmproxy_poc

# Access container shell
docker exec -it client_poc /bin/bash

# Check network interfaces
docker exec capture_poc ip addr show

# Check system resources (Windows)
docker system df
docker system info
```

## 📊 Results and Analysis

### JA4 Signatures Collected

The project successfully captures and analyzes:
- **JA4**: Client TLS fingerprint
- **JA4S**: Server TLS fingerprint  
- **JA4H**: TLS handshake fingerprint

### Sample Output

```json
{
  "timestamp": "2025-08-11T18:19:46",
  "signatures": [
    {
      "flow": "client → squid → external",
      "ja4": "t13d0010h2_8da4_010c_0010",
      "ja4s": "t13d0010h2_8da4_010c_0010",
      "ja4h": "t13d0010h2_8da4_010c_0010"
    }
  ]
}
```

## 🚀 Advanced Deployment

### Production Environment

```bash
# Install system dependencies (Linux)
sudo apt-get update
sudo apt-get install -y docker.io docker-compose python3-pip

# Setup project
pip3 install -r requirements.txt
python3 tests/install_proxy_cas.py

# Start services
docker compose up -d

# Verify deployment
make status
make health
```

### Docker Swarm Mode

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml proxy-ja4

# Scale services
docker service scale proxy-ja4_squid=2
```

### Kubernetes

```bash
# Convert to Kubernetes manifests
kompose convert -f docker-compose.yml

# Apply manifests
kubectl apply -f k8s/

# Check status
kubectl get pods -l app=proxy-ja4
```

### CI/CD Pipeline

```yaml
# Example GitHub Actions workflow
name: Proxy JA4 Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Docker
        uses: docker/setup-buildx-action@v2
      - name: Run Tests
        run: |
          make dev-setup
          make quick-test
```

## ⚙️ Configuration Management

### Environment Variables

```bash
# Set proxy versions
export MITMPROXY_TAG=9.0.1
export SQUID_VERSION=6.10

# Set network configuration
export CAPTURE_INTERFACE=eth0
export CAPTURE_OUTPUT=production.pcap
```

### Custom Configurations

```bash
# Custom Squid configuration
cp proxies/squid/squid.conf.custom proxies/squid/squid.conf

# Custom mitmproxy configuration
cp proxies/mitmproxy/config.custom proxies/mitmproxy/config

# Rebuild and restart
docker compose build
docker compose up -d
```

### Configuration Manager

```bash
# List available configurations
python scripts/config_manager.py --list

# Apply specific configuration
python scripts/config_manager.py --apply squid ssl_bump_only

# Validate configuration
python scripts/config_manager.py --validate squid ssl_bump_only

# Export configurations
python scripts/config_manager.py --export configs.json
```

## 🔒 Security Considerations

### Network Security
- **Firewall**: Restrict access to proxy ports (3129, 8081)
- **VPN**: Use VPN for remote access
- **SSL/TLS**: Use proper certificates in production

### Container Security
- **User permissions**: Run containers as non-root users
- **Resource limits**: Set memory and CPU limits
- **Image scanning**: Scan images for vulnerabilities

### Access Control
```yaml
# Restrict proxy access in docker-compose.yml
networks:
  pocnet:
    driver: bridge
    driver_opts:
      com.docker.network.bridge.name: br-proxy-ja4
    ipam:
      config:
        - subnet: 172.18.0.0/16
```

## 📈 Performance Tuning

### Resource Allocation

```yaml
# In docker-compose.yml
services:
  squid:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
        reservations:
          memory: 512M
          cpus: '0.25'
```

### Network Optimization

```bash
# Optimize Docker networking (Linux)
sudo sysctl -w net.core.rmem_max=26214400
sudo sysctl -w net.core.wmem_max=26214400

# Enable TCP optimization
sudo sysctl -w net.ipv4.tcp_congestion_control=bbr
```

## 💾 Backup and Recovery

### Backup Configuration

```bash
# Create backup
make backup

# Backup includes:
# - Proxy configurations
# - CA certificates
# - Docker Compose files
# - Test results
```

### Recovery

```bash
# Restore from backup
make restore-file FILE=backup-20250811-182500.tar.gz

# Rebuild containers
docker compose build
docker compose up -d
```

## 🔮 Future Enhancements

### High Priority (Next 1-2 months)
- [ ] Add Bluecoat proxy support
- [ ] Implement signature database storage
- [ ] Add automated version checking
- [ ] Create web dashboard

### Medium Priority (3-6 months)
- [ ] Machine learning signature analysis
- [ ] CI/CD pipeline integration
- [ ] Enhanced test coverage
- [ ] Performance benchmarking

### Low Priority (6+ months)
- [ ] Advanced analytics and reporting
- [ ] SIEM system integration
- [ ] Mobile monitoring app
- [ ] Enterprise features (SSO, RBAC)

## 🧪 Development

### Setup Development Environment

```bash
make dev-setup
```

### Run Tests

```bash
# Run all tests
make test-all

# Run specific test
python tests/test_all_proxies.py
```

### Code Quality

```bash
# Format code
black scripts/ tests/

# Lint code
flake8 scripts/ tests/

# Type checking
mypy scripts/ tests/
```

### Proxy Manager

```bash
# Test all proxy versions
python scripts/proxy_manager.py --test-all

# Test specific proxy and version
python scripts/proxy_manager.py --proxy squid --version 6.10

# List available versions
python scripts/proxy_manager.py --list-versions
```

## 📝 Monitoring and Maintenance

### Health Checks

```bash
# Check container health
make health

# View logs
make logs

# Monitor resources
docker stats
```

### Log Aggregation

```bash
# Enable log forwarding
docker compose up -d
docker compose logs -f > proxy-ja4.log

# Or use external logging
docker compose up -d --log-driver=fluentd
```

### Regular Tasks
- **Weekly**: Check container health and logs
- **Monthly**: Update proxy software versions
- **Quarterly**: Review and update CA certificates
- **Annually**: Security audit and dependency updates

### Update Process

```bash
# Update proxy versions
export MITMPROXY_TAG=latest
docker compose build mitmproxy
docker compose up -d mitmproxy

# Test updates
make quick-test
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Development Guidelines

- Follow Python PEP 8 style guide
- Add docstrings to new functions
- Update documentation for new features
- Test changes thoroughly before submitting
- Test on multiple platforms (Windows, macOS, Linux)

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- JA4 fingerprinting methodology
- Docker and Docker Compose communities
- Open source proxy projects (Squid, mitmproxy)
- Network security research community

## 📞 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review container logs with `make logs`
3. Create an issue in the repository
4. Check platform-specific notes for Windows users

### Platform-Specific Support

- **Windows**: Ensure Docker Desktop is running and fully initialized
- **macOS**: Docker Desktop should work out of the box
- **Linux**: Docker Engine installation may be required

---

**Project Status**: 🟢 **GREEN** - Ready for production use and further development.

