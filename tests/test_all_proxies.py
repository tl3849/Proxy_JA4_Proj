#!/usr/bin/env python3
"""
Comprehensive test script for TLS intercepting proxies:
- Direct (no proxy)
- Squid (with SSL bumping)
- mitmproxy (with TLS interception)

This script tests each proxy and collects JA4 signatures for analysis.
"""

import os
import sys
import time
import json
import subprocess
import requests
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Test configuration
TEST_HOSTS = [
    "http://httpbin.org/get",
    "https://httpbin.org/get",
    "http://example.com",
    "https://example.com"
]

PROXIES = [
    {
        "name": "direct",
        "env": None,
        "proxy_env": {},
        "description": "Direct connection (no proxy)"
    },
    {
        "name": "squid",
        "env": {
            "http_proxy": "http://squid_poc:3128",   # HTTP traffic
            "https_proxy": "http://squid_poc:3128"   # HTTPS traffic with SSL bumping
        },
        "description": "Squid proxy with SSL bump"
    },
    {
        "name": "mitmproxy",
        "env": {
            "http_proxy": "http://mitmproxy_poc:8080",
            "https_proxy": "http://mitmproxy_poc:8080"
        },
        "description": "mitmproxy with TLS interception"
    }
]

def log(message):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def check_proxy_health(proxy_name, port):
    """Check if proxy is healthy"""
    try:
        # Use container names instead of localhost for health checks
        host_mapping = {
            "squid": "squid_poc",
            "mitmproxy": "mitmproxy_poc"
        }
        
        if proxy_name not in host_mapping:
            return False
            
        host = host_mapping[proxy_name]
        
        if proxy_name == "squid":
            # Check the single port for Squid (supports both HTTP and HTTPS)
            try:
                response = requests.get(f"http://{host}:3128", timeout=5)
                return response.status_code < 500
            except Exception as e:
                log(f"Squid health check failed: {e}")
                return False
        else:
            # Use the internal container port for mitmproxy
            internal_port = 8080
            response = requests.get(f"http://{host}:{internal_port}", timeout=5)
            return response.status_code < 500  # Any response means the proxy is reachable
    except Exception as e:
        log(f"Health check failed for {proxy_name}: {e}")
        return False

def test_proxy(proxy_config):
    """Test a single proxy configuration"""
    proxy_name = proxy_config["name"]
    log(f"Testing {proxy_name}: {proxy_config['description']}")
    
    results = []
    
    # Check proxy health first
    if proxy_name != "direct":
        port_mapping = {
            "squid": 3129,
            "mitmproxy": 8081
        }
        
        if not check_proxy_health(proxy_name, port_mapping[proxy_name]):
            log(f"Warning: {proxy_name} health check failed, but continuing with test")
    
    # Test each host
    for host in TEST_HOSTS:
        log(f"  Testing {host} through {proxy_name}")
        
        try:
            # Set proxy environment if specified
            env = os.environ.copy()
            if proxy_config.get("env"):
                env.update(proxy_config["env"])
            
            # Make request using curl
            cmd = ["curl", "-sS", "-D", "/dev/stderr", "-o", "/dev/null", 
                   host, "--max-time", "15"]
            
            result = subprocess.run(
                cmd, 
                env=env if proxy_config.get("env") else None,
                capture_output=True, 
                text=True,
                check=False
            )
            
            success = result.returncode == 0
            log(f"    {'✓' if success else '✗'} {host} - {'Success' if success else 'Failed'}")
            
            results.append({
                "proxy": proxy_name,
                "url": host,
                "success": success,
                "return_code": result.returncode,
                "stderr": result.stderr if not success else None,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            log(f"    ✗ {host} - Exception: {e}")
            results.append({
                "proxy": proxy_name,
                "url": host,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
    
    return results

def run_all_tests():
    """Run tests for all proxies"""
    log("Starting comprehensive proxy test suite")
    log(f"Testing {len(PROXIES)} proxy configurations")
    log(f"Testing {len(TEST_HOSTS)} hosts per proxy")
    
    all_results = []
    
    for proxy_config in PROXIES:
        log(f"\n{'='*60}")
        proxy_results = test_proxy(proxy_config)
        all_results.extend(proxy_results)
        
        # Summary for this proxy
        success_count = sum(1 for r in proxy_results if r["success"])
        total_count = len(proxy_results)
        log(f"Proxy {proxy_config['name']}: {success_count}/{total_count} tests passed")
    
    # Overall summary
    log(f"\n{'='*60}")
    log("OVERALL TEST SUMMARY")
    log(f"{'='*60}")
    
    for proxy_config in PROXIES:
        proxy_name = proxy_config["name"]
        proxy_results = [r for r in all_results if r["proxy"] == proxy_name]
        success_count = sum(1 for r in proxy_results if r["success"])
        total_count = len(proxy_results)
        log(f"{proxy_name:12}: {success_count:2}/{total_count} tests passed")
    
    # Save results
    results_file = project_root / "captures" / "comprehensive_test_results.json"
    results_file.parent.mkdir(exist_ok=True)
    
    with open(results_file, 'w') as f:
        json.dump({
            "test_run": {
                "timestamp": datetime.now().isoformat(),
                "total_proxies": len(PROXIES),
                "total_tests": len(all_results),
                "successful_tests": sum(1 for r in all_results if r["success"])
            },
            "proxy_configs": PROXIES,
            "test_hosts": TEST_HOSTS,
            "results": all_results
        }, f, indent=2)
    
    log(f"\nDetailed results saved to: {results_file}")
    log("Test suite completed!")
    
    return all_results

def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print(__doc__)
        print("\nUsage: python test_all_proxies.py")
        print("This script will test all configured proxies and save results.")
        return
    
    try:
        results = run_all_tests()
        
        # Exit with error code if any tests failed
        failed_tests = sum(1 for r in results if not r["success"])
        if failed_tests > 0:
            log(f"Warning: {failed_tests} tests failed")
            sys.exit(1)
        else:
            log("All tests passed successfully!")
            
    except KeyboardInterrupt:
        log("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        log(f"Test suite failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
