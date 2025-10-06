"""
PortmanAI - Intelligent port and switch monitoring and management

Provides AI-powered analysis of network ports, switches, and traffic patterns.
"""

import logging
import asyncio
from typing import Dict, List, Optional
from datetime import datetime
import psutil
import socket

logger = logging.getLogger(__name__)


class PortmanAI:
    """
    AI-powered port monitoring and management system
    
    Monitors network ports, analyzes traffic, and provides intelligent
    recommendations for switch and port configuration.
    """
    
    def __init__(self):
        self.monitored_ports: Dict[int, Dict] = {}
        self.port_statistics: Dict[int, Dict] = {}
        self.monitoring_active = False
        self.anomaly_threshold = 0.8
        
    async def start_monitoring(self, ports: Optional[List[int]] = None):
        """
        Start monitoring network ports
        
        Args:
            ports: List of ports to monitor (None for all active ports)
        """
        logger.info("Starting PortmanAI monitoring...")
        self.monitoring_active = True
        
        while self.monitoring_active:
            try:
                await self._collect_port_statistics(ports)
                await self._analyze_traffic_patterns()
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(5)
    
    def stop_monitoring(self):
        """Stop port monitoring"""
        logger.info("Stopping PortmanAI monitoring...")
        self.monitoring_active = False
    
    async def _collect_port_statistics(self, ports: Optional[List[int]] = None):
        """Collect statistics for monitored ports"""
        try:
            # Get all network connections
            connections = psutil.net_connections()
            
            for conn in connections:
                # Filter by specified ports if provided
                if ports and conn.laddr.port not in ports:
                    continue
                
                port = conn.laddr.port
                
                if port not in self.port_statistics:
                    self.port_statistics[port] = {
                        "connections": 0,
                        "first_seen": datetime.now(),
                        "last_seen": datetime.now(),
                        "protocols": set(),
                        "states": {}
                    }
                
                stats = self.port_statistics[port]
                stats["connections"] += 1
                stats["last_seen"] = datetime.now()
                stats["protocols"].add(conn.type.name if hasattr(conn.type, 'name') else str(conn.type))
                
                # Track connection states
                state = conn.status
                if state not in stats["states"]:
                    stats["states"][state] = 0
                stats["states"][state] += 1
                
        except Exception as e:
            logger.error(f"Error collecting port statistics: {e}")
    
    async def _analyze_traffic_patterns(self):
        """Analyze traffic patterns and detect anomalies"""
        try:
            for port, stats in self.port_statistics.items():
                # Simple anomaly detection based on connection count
                if stats["connections"] > 1000:  # Threshold for high traffic
                    logger.warning(f"High traffic detected on port {port}: {stats['connections']} connections")
                    
                # Check for unusual states
                if "CLOSE_WAIT" in stats["states"] and stats["states"]["CLOSE_WAIT"] > 10:
                    logger.warning(f"Port {port} has {stats['states']['CLOSE_WAIT']} connections in CLOSE_WAIT state")
                    
        except Exception as e:
            logger.error(f"Error analyzing traffic patterns: {e}")
    
    def get_port_info(self, port: int) -> Optional[Dict]:
        """Get detailed information about a specific port"""
        try:
            # Get service name for well-known ports
            try:
                service = socket.getservbyport(port)
            except:
                service = "Unknown"
            
            info = {
                "port": port,
                "service": service,
                "statistics": self.port_statistics.get(port, {})
            }
            
            # Get current connections on this port
            connections = psutil.net_connections()
            active_connections = [
                {
                    "local": f"{conn.laddr.ip}:{conn.laddr.port}",
                    "remote": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "N/A",
                    "status": conn.status,
                    "pid": conn.pid
                }
                for conn in connections if conn.laddr.port == port
            ]
            
            info["active_connections"] = active_connections
            info["connection_count"] = len(active_connections)
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting port info: {e}")
            return None
    
    def get_all_active_ports(self) -> List[Dict]:
        """Get information about all active ports"""
        try:
            ports = {}
            connections = psutil.net_connections()
            
            for conn in connections:
                port = conn.laddr.port
                
                if port not in ports:
                    ports[port] = {
                        "port": port,
                        "connections": 0,
                        "protocols": set(),
                        "states": set()
                    }
                
                ports[port]["connections"] += 1
                ports[port]["protocols"].add(conn.type.name if hasattr(conn.type, 'name') else str(conn.type))
                ports[port]["states"].add(conn.status)
            
            # Convert sets to lists for JSON serialization
            result = []
            for port_info in ports.values():
                port_info["protocols"] = list(port_info["protocols"])
                port_info["states"] = list(port_info["states"])
                result.append(port_info)
            
            return sorted(result, key=lambda x: x["port"])
            
        except Exception as e:
            logger.error(f"Error getting active ports: {e}")
            return []
    
    def analyze_port_health(self, port: int) -> Dict:
        """
        Analyze the health of a specific port
        
        Returns health score and recommendations
        """
        try:
            port_info = self.get_port_info(port)
            if not port_info:
                return {"error": "Port not found"}
            
            health_score = 100
            recommendations = []
            issues = []
            
            stats = port_info.get("statistics", {})
            active_conns = port_info.get("connection_count", 0)
            
            # Check for high connection count
            if active_conns > 100:
                health_score -= 20
                issues.append(f"High connection count: {active_conns}")
                recommendations.append("Consider rate limiting or load balancing")
            
            # Check for CLOSE_WAIT states
            if stats and "states" in stats:
                close_wait = stats["states"].get("CLOSE_WAIT", 0)
                if close_wait > 10:
                    health_score -= 15
                    issues.append(f"High CLOSE_WAIT count: {close_wait}")
                    recommendations.append("Application may not be closing connections properly")
            
            # Check for TIME_WAIT states
            if stats and "states" in stats:
                time_wait = stats["states"].get("TIME_WAIT", 0)
                if time_wait > 50:
                    health_score -= 10
                    issues.append(f"High TIME_WAIT count: {time_wait}")
                    recommendations.append("Consider adjusting TCP TIME_WAIT timeout")
            
            return {
                "port": port,
                "health_score": max(0, health_score),
                "status": "healthy" if health_score >= 80 else "warning" if health_score >= 50 else "critical",
                "issues": issues,
                "recommendations": recommendations,
                "active_connections": active_conns
            }
            
        except Exception as e:
            logger.error(f"Error analyzing port health: {e}")
            return {"error": str(e)}
    
    def get_switch_recommendations(self) -> List[str]:
        """
        Get AI-powered recommendations for switch configuration
        """
        recommendations = []
        
        try:
            all_ports = self.get_all_active_ports()
            
            # Analyze overall network health
            high_traffic_ports = [p for p in all_ports if p["connections"] > 100]
            if high_traffic_ports:
                recommendations.append(
                    f"Consider VLAN segmentation for high-traffic ports: {[p['port'] for p in high_traffic_ports]}"
                )
            
            # Check for common service ports
            common_services = [80, 443, 22, 3306, 5432, 6379]
            exposed_services = [p for p in all_ports if p["port"] in common_services]
            
            if exposed_services:
                recommendations.append(
                    "Ensure proper firewall rules for exposed service ports"
                )
            
            # Check for unusual ports
            unusual_ports = [p for p in all_ports if p["port"] > 49152]  # Dynamic/private ports
            if len(unusual_ports) > 20:
                recommendations.append(
                    f"Large number of dynamic ports active ({len(unusual_ports)}). Monitor for potential security issues."
                )
            
            if not recommendations:
                recommendations.append("Network configuration appears optimal")
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            recommendations.append("Error analyzing network configuration")
        
        return recommendations
    
    def get_monitoring_summary(self) -> Dict:
        """Get summary of monitoring data"""
        return {
            "monitoring_active": self.monitoring_active,
            "monitored_ports_count": len(self.port_statistics),
            "total_connections": sum(s.get("connections", 0) for s in self.port_statistics.values()),
            "statistics": self.port_statistics
        }
