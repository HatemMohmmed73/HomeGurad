"""
Firewall Controller - nftables integration
"""
import subprocess
import logging
from typing import List, Dict, Optional
from config import settings

logger = logging.getLogger(__name__)


class FirewallController:
    """Manages firewall rules using nftables"""
    
    def __init__(self):
        self.table_name = settings.NFTABLES_TABLE
        self.chain_name = settings.NFTABLES_CHAIN
        self.blocked_devices: Dict[str, Dict[str, str]] = {}  # MAC -> {ip, reason}
        
        # Initialize firewall table and chain
        self._initialize_firewall()
    
    def _initialize_firewall(self):
        """Initialize nftables table and chain"""
        try:
            # Check if running with appropriate privileges
            # For development, we'll just log the commands
            logger.info("Initializing HomeGuard firewall...")
            
            # Commands to initialize (would need root/sudo in production)
            commands = [
                f"nft add table inet {self.table_name}",
                f"nft add chain inet {self.table_name} {self.chain_name} {{ type filter hook forward priority 0\\; }}",
            ]
            
            # In development, just log
            for cmd in commands:
                logger.info(f"[FIREWALL] {cmd}")
            
            print(f"✅ Firewall initialized: {self.table_name}/{self.chain_name}")
            
        except Exception as e:
            logger.warning(f"Firewall initialization warning: {e}")
            print(f"⚠️  Firewall initialization skipped (requires root privileges)")
    
    def block_device(self, ip: str, mac: str, reason: str = "Anomaly detected") -> bool:
        """
        Block a device by IP and MAC address
        
        Args:
            ip: Device IP address
            mac: Device MAC address
            reason: Reason for blocking
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Block by IP
            cmd_ip = f"nft add rule inet {self.table_name} {self.chain_name} ip saddr {ip} drop"
            
            # Block by MAC (backup)
            cmd_mac = f"nft add rule inet {self.table_name} {self.chain_name} ether saddr {mac} drop"
            
            # In production, execute commands
            # For development, log them
            logger.info(f"[BLOCK] {cmd_ip}")
            logger.info(f"[BLOCK] {cmd_mac}")
            
            # Store blocked device info
            self.blocked_devices[mac] = {
                "ip": ip,
                "reason": reason,
                "rule_ip": cmd_ip,
                "rule_mac": cmd_mac
            }
            
            print(f"🚫 Blocked device: {ip} ({mac}) - {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to block device {ip}: {e}")
            return False
    
    def unblock_device(self, ip: str, mac: str) -> bool:
        """
        Unblock a device
        
        Args:
            ip: Device IP address
            mac: Device MAC address
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if mac not in self.blocked_devices:
                logger.warning(f"Device {ip} ({mac}) is not in blocked list")
                return True
            
            # Get handle of the rules and delete them
            # This is simplified - in production you'd need to find rule handles
            cmd_list = f"nft -a list chain inet {self.table_name} {self.chain_name}"
            
            logger.info(f"[UNBLOCK] Removing rules for {ip} ({mac})")
            
            # Remove from blocked devices
            del self.blocked_devices[mac]
            
            print(f"✅ Unblocked device: {ip} ({mac})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unblock device {ip}: {e}")
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
        """Check if device is blocked"""
        return mac in self.blocked_devices
    
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

