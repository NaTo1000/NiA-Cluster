#!/usr/bin/env python3
"""
NiA-Cluster GUI Suite
Internal WiFi/BLE/ESP Clustering Manager with Port Control and Security
"""

import os
import sys
import logging
import json
import socket
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

# Configure logging
LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, f'cluster_{datetime.now().strftime("%Y%m%d")}.log')),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ClusterNode:
    """Represents a node in the cluster"""
    
    def __init__(self, node_id: str, node_type: str, ip_address: str, port: int):
        self.node_id = node_id
        self.node_type = node_type  # WiFi, BLE, ESP
        self.ip_address = ip_address
        self.port = port
        self.status = "offline"
        self.last_seen = None
        self.security_token = None
    
    def to_dict(self) -> Dict:
        return {
            'node_id': self.node_id,
            'node_type': self.node_type,
            'ip_address': self.ip_address,
            'port': self.port,
            'status': self.status,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None
        }


class ClusterManager:
    """Manages cluster nodes and connections"""
    
    def __init__(self):
        self.nodes: Dict[str, ClusterNode] = {}
        self.data_dir = os.path.join(os.path.dirname(__file__), 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        self.config_file = os.path.join(self.data_dir, 'cluster_config.json')
        self.load_config()
        
    def load_config(self):
        """Load cluster configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    for node_data in config.get('nodes', []):
                        node = ClusterNode(
                            node_data['node_id'],
                            node_data['node_type'],
                            node_data['ip_address'],
                            node_data['port']
                        )
                        self.nodes[node.node_id] = node
                logger.info(f"Loaded {len(self.nodes)} nodes from configuration")
        except Exception as e:
            logger.error(f"Error loading config: {e}")
    
    def save_config(self):
        """Save cluster configuration to file"""
        try:
            config = {
                'nodes': [node.to_dict() for node in self.nodes.values()],
                'last_updated': datetime.now().isoformat()
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def add_node(self, node: ClusterNode) -> bool:
        """Add a new node to the cluster"""
        if node.node_id in self.nodes:
            logger.warning(f"Node {node.node_id} already exists")
            return False
        self.nodes[node.node_id] = node
        self.save_config()
        logger.info(f"Added node {node.node_id} ({node.node_type})")
        return True
    
    def remove_node(self, node_id: str) -> bool:
        """Remove a node from the cluster"""
        if node_id in self.nodes:
            del self.nodes[node_id]
            self.save_config()
            logger.info(f"Removed node {node_id}")
            return True
        return False
    
    def get_node(self, node_id: str) -> Optional[ClusterNode]:
        """Get a specific node"""
        return self.nodes.get(node_id)
    
    def get_all_nodes(self) -> List[ClusterNode]:
        """Get all nodes"""
        return list(self.nodes.values())
    
    def update_node_status(self, node_id: str, status: str):
        """Update node status"""
        if node_id in self.nodes:
            self.nodes[node_id].status = status
            self.nodes[node_id].last_seen = datetime.now()
            logger.info(f"Node {node_id} status updated to {status}")


class ClusterGUI:
    """Main GUI application for cluster management"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("NiA-Cluster Management Suite")
        self.root.geometry("1000x700")
        
        self.manager = ClusterManager()
        self.setup_ui()
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self.monitor_nodes, daemon=True)
        self.monitor_thread.start()
        
        logger.info("Cluster GUI initialized")
    
    def setup_ui(self):
        """Setup the user interface"""
        # Create main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="NiA-Cluster Management Suite", 
                               font=('Helvetica', 16, 'bold'))
        title_label.grid(row=0, column=0, pady=10)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Nodes tab
        self.nodes_frame = ttk.Frame(notebook)
        notebook.add(self.nodes_frame, text="Cluster Nodes")
        self.setup_nodes_tab()
        
        # Monitoring tab
        self.monitoring_frame = ttk.Frame(notebook)
        notebook.add(self.monitoring_frame, text="Monitoring")
        self.setup_monitoring_tab()
        
        # Configuration tab
        self.config_frame = ttk.Frame(notebook)
        notebook.add(self.config_frame, text="Configuration")
        self.setup_config_tab()
        
        # Logs tab
        self.logs_frame = ttk.Frame(notebook)
        notebook.add(self.logs_frame, text="Logs")
        self.setup_logs_tab()
    
    def setup_nodes_tab(self):
        """Setup nodes management tab"""
        # Toolbar
        toolbar = ttk.Frame(self.nodes_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(toolbar, text="Add Node", command=self.add_node_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Remove Node", command=self.remove_node).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Refresh", command=self.refresh_nodes_list).pack(side=tk.LEFT, padx=2)
        
        # Nodes list
        list_frame = ttk.Frame(self.nodes_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create treeview
        columns = ('ID', 'Type', 'IP Address', 'Port', 'Status', 'Last Seen')
        self.nodes_tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        for col in columns:
            self.nodes_tree.heading(col, text=col)
            self.nodes_tree.column(col, width=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.nodes_tree.yview)
        self.nodes_tree.configure(yscrollcommand=scrollbar.set)
        
        self.nodes_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Initial population
        self.refresh_nodes_list()
    
    def setup_monitoring_tab(self):
        """Setup monitoring tab"""
        # Status display
        status_frame = ttk.LabelFrame(self.monitoring_frame, text="Cluster Status", padding="10")
        status_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.status_text = scrolledtext.ScrolledText(status_frame, height=20, state='disabled')
        self.status_text.pack(fill=tk.BOTH, expand=True)
        
        # Refresh button
        ttk.Button(self.monitoring_frame, text="Refresh Status", 
                  command=self.refresh_status).pack(pady=5)
    
    def setup_config_tab(self):
        """Setup configuration tab"""
        config_frame = ttk.LabelFrame(self.config_frame, text="Server Configuration", padding="10")
        config_frame.pack(fill=tk.BOTH, padx=5, pady=5)
        
        # Port configuration
        ttk.Label(config_frame, text="Control Port:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.control_port_var = tk.StringVar(value="8080")
        ttk.Entry(config_frame, textvariable=self.control_port_var).grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(config_frame, text="Secure Port:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.secure_port_var = tk.StringVar(value="8443")
        ttk.Entry(config_frame, textvariable=self.secure_port_var).grid(row=1, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(config_frame, text="API Port:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.api_port_var = tk.StringVar(value="5000")
        ttk.Entry(config_frame, textvariable=self.api_port_var).grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # Security settings
        security_frame = ttk.LabelFrame(self.config_frame, text="Security Settings", padding="10")
        security_frame.pack(fill=tk.BOTH, padx=5, pady=5)
        
        self.enable_auth_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(security_frame, text="Enable Authentication", 
                       variable=self.enable_auth_var).pack(anchor=tk.W)
        
        self.enable_encryption_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(security_frame, text="Enable Encryption", 
                       variable=self.enable_encryption_var).pack(anchor=tk.W)
        
        ttk.Button(self.config_frame, text="Save Configuration", 
                  command=self.save_configuration).pack(pady=10)
    
    def setup_logs_tab(self):
        """Setup logs display tab"""
        self.logs_text = scrolledtext.ScrolledText(self.logs_frame, height=30)
        self.logs_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Load recent logs
        self.load_logs()
    
    def add_node_dialog(self):
        """Show dialog to add a new node"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Node")
        dialog.geometry("400x300")
        
        frame = ttk.Frame(dialog, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Node ID:").grid(row=0, column=0, sticky=tk.W, pady=5)
        node_id_var = tk.StringVar()
        ttk.Entry(frame, textvariable=node_id_var).grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(frame, text="Node Type:").grid(row=1, column=0, sticky=tk.W, pady=5)
        node_type_var = tk.StringVar(value="WiFi")
        ttk.Combobox(frame, textvariable=node_type_var, 
                    values=["WiFi", "BLE", "ESP"]).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(frame, text="IP Address:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ip_var = tk.StringVar(value="192.168.1.100")
        ttk.Entry(frame, textvariable=ip_var).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(frame, text="Port:").grid(row=3, column=0, sticky=tk.W, pady=5)
        port_var = tk.StringVar(value="8080")
        ttk.Entry(frame, textvariable=port_var).grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5)
        
        def save_node():
            try:
                node = ClusterNode(
                    node_id_var.get(),
                    node_type_var.get(),
                    ip_var.get(),
                    int(port_var.get())
                )
                if self.manager.add_node(node):
                    self.refresh_nodes_list()
                    dialog.destroy()
                    messagebox.showinfo("Success", "Node added successfully")
                else:
                    messagebox.showerror("Error", "Node already exists")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to add node: {e}")
        
        ttk.Button(frame, text="Save", command=save_node).grid(row=4, column=0, pady=20)
        ttk.Button(frame, text="Cancel", command=dialog.destroy).grid(row=4, column=1, pady=20)
        
        frame.columnconfigure(1, weight=1)
    
    def remove_node(self):
        """Remove selected node"""
        selection = self.nodes_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a node to remove")
            return
        
        item = self.nodes_tree.item(selection[0])
        node_id = item['values'][0]
        
        if messagebox.askyesno("Confirm", f"Remove node {node_id}?"):
            if self.manager.remove_node(node_id):
                self.refresh_nodes_list()
                messagebox.showinfo("Success", "Node removed successfully")
    
    def refresh_nodes_list(self):
        """Refresh the nodes list display"""
        # Clear current items
        for item in self.nodes_tree.get_children():
            self.nodes_tree.delete(item)
        
        # Add all nodes
        for node in self.manager.get_all_nodes():
            last_seen = node.last_seen.strftime("%Y-%m-%d %H:%M:%S") if node.last_seen else "Never"
            self.nodes_tree.insert('', 'end', values=(
                node.node_id,
                node.node_type,
                node.ip_address,
                node.port,
                node.status,
                last_seen
            ))
    
    def refresh_status(self):
        """Refresh cluster status display"""
        self.status_text.config(state='normal')
        self.status_text.delete(1.0, tk.END)
        
        status_info = f"Cluster Status Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        status_info += "=" * 60 + "\n\n"
        
        nodes = self.manager.get_all_nodes()
        status_info += f"Total Nodes: {len(nodes)}\n"
        status_info += f"Online Nodes: {sum(1 for n in nodes if n.status == 'online')}\n"
        status_info += f"Offline Nodes: {sum(1 for n in nodes if n.status == 'offline')}\n\n"
        
        status_info += "Node Details:\n"
        status_info += "-" * 60 + "\n"
        for node in nodes:
            status_info += f"\nNode ID: {node.node_id}\n"
            status_info += f"  Type: {node.node_type}\n"
            status_info += f"  Address: {node.ip_address}:{node.port}\n"
            status_info += f"  Status: {node.status}\n"
            status_info += f"  Last Seen: {node.last_seen.strftime('%Y-%m-%d %H:%M:%S') if node.last_seen else 'Never'}\n"
        
        self.status_text.insert(1.0, status_info)
        self.status_text.config(state='disabled')
    
    def save_configuration(self):
        """Save application configuration"""
        try:
            config = {
                'control_port': int(self.control_port_var.get()),
                'secure_port': int(self.secure_port_var.get()),
                'api_port': int(self.api_port_var.get()),
                'enable_auth': self.enable_auth_var.get(),
                'enable_encryption': self.enable_encryption_var.get()
            }
            
            config_file = os.path.join(self.manager.data_dir, 'app_config.json')
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            messagebox.showinfo("Success", "Configuration saved successfully")
            logger.info("Application configuration saved")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
            logger.error(f"Error saving configuration: {e}")
    
    def load_logs(self):
        """Load and display recent logs"""
        try:
            log_file = os.path.join(LOG_DIR, f'cluster_{datetime.now().strftime("%Y%m%d")}.log')
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    logs = f.read()
                    self.logs_text.insert(1.0, logs)
        except Exception as e:
            logger.error(f"Error loading logs: {e}")
    
    def monitor_nodes(self):
        """Background thread to monitor node status"""
        while True:
            try:
                # Simulate node monitoring
                for node in self.manager.get_all_nodes():
                    # In a real implementation, this would ping nodes or check heartbeats
                    # For now, we'll just log the monitoring activity
                    pass
                time.sleep(10)  # Monitor every 10 seconds
            except Exception as e:
                logger.error(f"Error in monitoring thread: {e}")
                time.sleep(30)


def main():
    """Main entry point"""
    logger.info("Starting NiA-Cluster Management Suite")
    
    try:
        root = tk.Tk()
        app = ClusterGUI(root)
        root.mainloop()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
