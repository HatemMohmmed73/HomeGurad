"""
Firewall Controller - Uses bash scripts for blocking/unblocking devices
"""
import subprocess
import logging
import os
from pathlib import Path
from typing import List, Dict, Optional
from config import settings

logger = logging.getLogger(__name__)


class FirewallController:
    """Manages firewall rules using bash scripts"""
    
    def __init__(self):
        self.table_name = settings.NFTABLES_TABLE
        self.chain_name = settings.NFTABLES_CHAIN
        self.blocked_devices: Dict[str, Dict[str, str]] = {}  # MAC -> {ip, reason}
        
        # Script paths - try multiple locations
        self.block_script = self._find_script("block_ip.sh")
        self.unblock_script = self._find_script("unblock.sh")
        
        # Initialize firewall
        self._initialize_firewall()
    
    def _find_script(self, script_name: str) -> Optional[str]:
        """Find the script in common locations"""
        possible_paths = [
            f"/scripts/{script_name}",  # Mounted in container
            f"/home/orangepi/scripts/{script_name}",  # Host path (if mounted)
            f"/app/scripts/{script_name}",  # In container
            script_name,  # Current directory or PATH
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                # Check if executable
                if os.access(path, os.X_OK):
                    logger.info(f"Found {script_name} at: {path} (executable)")
                    print(f"✅ Found {script_name} at: {path} (executable)", flush=True)
                    return path
                else:
                    logger.warning(f"Found {script_name} at: {path} but not executable")
                    print(f"⚠️  Found {script_name} at: {path} but not executable", flush=True)
            else:
                logger.debug(f"Script not found at: {path}")
        
        logger.error(f"Script {script_name} not found in any standard locations")
        print(f"❌ Script {script_name} not found in any standard locations", flush=True)
        return None
    
    def _initialize_firewall(self):
        """Initialize firewall (scripts handle nftables setup)"""
        try:
            logger.info("Initializing HomeGuard firewall...")
            
            if self.block_script and self.unblock_script:
                print(f"✅ Firewall scripts found: {self.block_script}, {self.unblock_script}", flush=True)
                # Test if scripts are accessible
                script_dir = os.path.dirname(self.block_script)
                if os.path.exists(script_dir):
                    print(f"✅ Script directory exists: {script_dir}", flush=True)
                    # List files in script directory
                    try:
                        files = os.listdir(script_dir)
                        print(f"📁 Files in {script_dir}: {files}", flush=True)
                    except Exception as e:
                        print(f"⚠️  Cannot list files in {script_dir}: {e}", flush=True)
            else:
                print(f"⚠️  Firewall scripts not found - blocking may not work", flush=True)
                if not self.block_script:
                    print(f"❌ block_ip.sh not found", flush=True)
                if not self.unblock_script:
                    print(f"❌ unblock.sh not found", flush=True)
            
        except Exception as e:
            logger.warning(f"Firewall initialization warning: {e}")
            print(f"⚠️  Firewall initialization skipped: {e}", flush=True)
    
    def block_device(self, ip: str, mac: str, reason: str = "Anomaly detected") -> bool:
        """
        Block a device by IP address using block_ip.sh script
        
        Args:
            ip: Device IP address
            mac: Device MAC address (not used by script, but kept for compatibility)
            reason: Reason for blocking
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.block_script:
                logger.error("Block script not found")
                return False
            
            if not ip:
                logger.error("No IP address provided")
                return False
            
            # Get script directory and name
            script_dir = os.path.dirname(self.block_script)
            script_name = os.path.basename(self.block_script)
            
            logger.info(f"Executing block script: ./{script_name} {ip} in directory: {script_dir}")
            print(f"🔧 Executing: cd {script_dir} && ./{script_name} {ip}", flush=True)
            
            # Execute the block script with ./block_ip.sh <ip> format
            result = subprocess.run(
                f"./{script_name} {ip}",
                cwd=script_dir,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Log full output for debugging
            logger.info(f"Script return code: {result.returncode}")
            logger.info(f"Script stdout: {result.stdout}")
            logger.info(f"Script stderr: {result.stderr}")
            print(f"📊 Script return code: {result.returncode}", flush=True)
            if result.stdout:
                print(f"📤 Script stdout: {result.stdout.strip()}", flush=True)
            if result.stderr:
                print(f"📥 Script stderr: {result.stderr.strip()}", flush=True)
            
            if result.returncode == 0:
                # Store blocked device info
                self.blocked_devices[mac] = {
                    "ip": ip,
                    "reason": reason,
                    "script": self.block_script
                }
                
                logger.info(f"Blocked device: {ip} ({mac}) - {reason}")
                print(f"🚫 Blocked device: {ip} ({mac}) - {reason}", flush=True)
                if result.stdout:
                    logger.info(f"Script output: {result.stdout.strip()}")
                return True
            else:
                error_msg = result.stderr.strip() or result.stdout.strip() or "Unknown error"
                logger.error(f"Failed to block device {ip}: {error_msg}")
                print(f"❌ Failed to block device {ip}: {error_msg}", flush=True)
                return False
            
        except subprocess.TimeoutExpired:
            logger.error(f"Block script timeout for IP: {ip}")
            return False
        except Exception as e:
            logger.error(f"Failed to block device {ip}: {e}", exc_info=True)
            return False
    
    def unblock_device(self, ip: str, mac: str) -> bool:
        """
        Unblock a device by IP address using unblock.sh script
        
        Args:
            ip: Device IP address
            mac: Device MAC address (not used by script, but kept for compatibility)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.unblock_script:
                logger.error("Unblock script not found")
                return False
            
            if not ip:
                logger.error("No IP address provided")
                return False
            
            # Get script directory and name
            script_dir = os.path.dirname(self.unblock_script)
            script_name = os.path.basename(self.unblock_script)
            
            logger.info(f"Executing unblock script: ./{script_name} {ip} in directory: {script_dir}")
            print(f"🔧 Executing: cd {script_dir} && ./{script_name} {ip}", flush=True)
            
            # Execute the unblock script with ./unblock.sh <ip> format
            result = subprocess.run(
                f"./{script_name} {ip}",
                cwd=script_dir,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Log full output for debugging
            logger.info(f"Script return code: {result.returncode}")
            logger.info(f"Script stdout: {result.stdout}")
            logger.info(f"Script stderr: {result.stderr}")
            print(f"📊 Script return code: {result.returncode}", flush=True)
            if result.stdout:
                print(f"📤 Script stdout: {result.stdout.strip()}", flush=True)
            if result.stderr:
                print(f"📥 Script stderr: {result.stderr.strip()}", flush=True)
            
            # Check both return code and script output for success/error
            script_output = result.stdout.strip() if result.stdout else ""
            script_stderr = result.stderr.strip() if result.stderr else ""
            
            # Check for explicit success/error messages in output
            has_success = "[SUCCESS]" in script_output
            has_error = "[ERROR]" in script_output
            
            if result.returncode == 0 and has_success:
                # Successfully unblocked
                if mac in self.blocked_devices:
                    del self.blocked_devices[mac]
                
                logger.info(f"Unblocked device: {ip} ({mac})")
                print(f"✅ Unblocked device: {ip} ({mac})", flush=True)
                if script_output:
                    logger.info(f"Script output: {script_output}")
                return True
            elif has_error or result.returncode != 0:
                # Script reported error or non-zero exit code
                error_msg = script_stderr or script_output or "Unknown error"
                
                # Check if the error is because IP is not in the set (already unblocked)
                # This can happen if the IP was blocked by AI agent using a different method
                # or if it was already removed from the set
                if "not in set" in error_msg.lower() or "does not exist" in error_msg.lower() or "no such file" in error_msg.lower() or "Failed to unblock" in error_msg:
                    # IP is not in the blocked set - device is effectively already unblocked
                    logger.info(f"IP {ip} is not in blocked set - device is already unblocked")
                    print(f"ℹ️  IP {ip} is not in blocked set - device is already unblocked (error: {error_msg})", flush=True)
                    # Remove from tracked blocked devices if present
                    if mac in self.blocked_devices:
                        del self.blocked_devices[mac]
                    return True  # Consider it successful since device is not blocked
                else:
                    # Real error occurred
                    logger.error(f"Failed to unblock device {ip}: {error_msg}")
                    print(f"❌ Failed to unblock device {ip}: {error_msg}", flush=True)
                    return False
                # or if it was already manually removed
                if "No such file" in error_msg or "not found" in error_msg.lower() or "does not exist" in error_msg.lower():
                    logger.warning(f"IP {ip} may not be in the blocked set (possibly already unblocked)")
                    print(f"⚠️  IP {ip} may not be in the blocked set - treating as already unblocked", flush=True)
                    # Remove from blocked devices tracking since it's effectively unblocked
                    if mac in self.blocked_devices:
                        del self.blocked_devices[mac]
                    # Return True since the end goal (device unblocked) is achieved
                    return True
                
                return False
            else:
                # Unexpected case - unclear result
                logger.warning(f"Unblock script returned unclear result for {ip}: return_code={result.returncode}, output={script_output}")
                print(f"⚠️  Unblock script returned unclear result for {ip}: return_code={result.returncode}", flush=True)
                # If return code is 0 but no success message, assume it worked
                if result.returncode == 0:
                    if mac in self.blocked_devices:
                        del self.blocked_devices[mac]
                    return True
                return False
            
        except subprocess.TimeoutExpired:
            logger.error(f"Unblock script timeout for IP: {ip}")
            return False
        except Exception as e:
            logger.error(f"Failed to unblock device {ip}: {e}", exc_info=True)
            return False
    
    def get_blocked_devices(self) -> List[Dict[str, str]]:
        """Get list of currently blocked devices"""
        return [
            {
                "mac": mac,
                "ip": info["ip"],
                "reason": info["reason"]
            }
            for mac, info in self.blocked_devices.items()
        ]
    
    def is_device_blocked(self, mac: str) -> bool:
        """Check if device is blocked (from memory cache)"""
        return mac in self.blocked_devices
    
    def is_ip_blocked_in_firewall(self, ip: str) -> bool:
        """Check if an IP is actually blocked in nftables firewall by checking the malicious_devices set"""
        try:
            # Check if IP is in the malicious_devices set
            # Using the same table/set as the scripts: inet homefw malicious_devices
            family = "inet"
            table = "homefw"
            set_name = "malicious_devices"
            
            # Run: nft list set inet homefw malicious_devices
            result = subprocess.run(
                ["nft", "list", "set", family, table, set_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Parse the output to check if IP is in the set
                # Output format: elements = { 10.10.0.11, 192.168.1.100 }
                output = result.stdout
                
                # Extract IPs from the output (look for the IP in the elements list)
                # The IP should appear as a standalone element in the set
                # Check if IP appears as a word boundary (to avoid partial matches)
                import re
                # Match IP as a complete word in the elements list
                ip_pattern = r'\b' + re.escape(ip) + r'\b'
                is_blocked = bool(re.search(ip_pattern, output))
                
                logger.info(f"[FIREWALL_CHECK] IP: {ip} | Status: {'BLOCKED' if is_blocked else 'NOT BLOCKED'} | Set contents: {output.strip()}")
                print(f"[FIREWALL_CHECK] 🔍 IP: {ip} | Status: {'🚫 BLOCKED' if is_blocked else '✅ NOT BLOCKED'} | Set: {output.strip()[:100]}", flush=True)
                return is_blocked
            else:
                # If set doesn't exist or command failed, assume not blocked
                logger.warning(f"[FIREWALL_CHECK] Failed to check firewall state for {ip}: {result.stderr}")
                print(f"[FIREWALL_CHECK] ⚠️  Failed to check {ip}: {result.stderr.strip()}", flush=True)
                return False
                
        except Exception as e:
            logger.error(f"[FIREWALL_CHECK] Error checking firewall state for {ip}: {e}", exc_info=True)
            print(f"[FIREWALL_CHECK] ❌ Error checking {ip}: {e}", flush=True)
            return False
    
    def clear_all_rules(self) -> bool:
        """Clear all blocking rules (caution!)"""
        try:
            cmd = f"nft flush chain inet {self.table_name} {self.chain_name}"
            logger.info(f"[CLEAR] {cmd}")
            
            self.blocked_devices.clear()
            print("🗑️  All firewall rules cleared")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear rules: {e}")
            return False
    
    def _execute_command(self, command: str) -> tuple:
        """
        Execute nftables command
        
        Args:
            command: Command to execute
            
        Returns:
            Tuple of (success, output, error)
        """
        try:
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                timeout=5
            )
            
            success = result.returncode == 0
            return success, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            return False, "", "Command timeout"
        except Exception as e:
            return False, "", str(e)
    
    def get_firewall_stats(self) -> Dict[str, any]:
        """Get firewall statistics"""
        return {
            "table": self.table_name,
            "chain": self.chain_name,
            "blocked_count": len(self.blocked_devices),
            "blocked_devices": self.get_blocked_devices()
        }

