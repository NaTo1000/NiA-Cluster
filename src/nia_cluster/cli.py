"""
Command Line Interface for NiA-Cluster
"""

import sys
import logging
import argparse
from nia_cluster import ClusterManager


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='NiA-Cluster - Advanced Networking Cluster Manager'
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start cluster services')
    
    # Stop command
    stop_parser = subparsers.add_parser('stop', help='Stop cluster services')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Get cluster status')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Manage configuration')
    config_parser.add_argument('--show', action='store_true', help='Show current configuration')
    config_parser.add_argument('--init', action='store_true', help='Initialize default configuration')
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        if args.command == 'start':
            logger.info("Starting NiA-Cluster...")
            manager = ClusterManager(args.config)
            manager.start()
            
            # Keep running
            logger.info("Press Ctrl+C to stop")
            try:
                import time
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Stopping NiA-Cluster...")
                manager.stop()
        
        elif args.command == 'stop':
            logger.info("Stop command - not implemented for remote instances")
            # In production, this would connect to running instance and stop it
        
        elif args.command == 'status':
            logger.info("Getting cluster status...")
            manager = ClusterManager(args.config)
            status = manager.get_status()
            
            print("\nNiA-Cluster Status:")
            print("-" * 50)
            for component, info in status.items():
                print(f"\n{component.upper()}:")
                print_dict(info, indent=2)
        
        elif args.command == 'config':
            from nia_cluster.config import ConfigManager
            
            if args.init:
                logger.info("Initializing default configuration...")
                config = ConfigManager()
                config_path = 'config/cluster.yaml'
                config.save(config_path)
                logger.info(f"Configuration saved to {config_path}")
            
            elif args.show:
                config = ConfigManager(args.config)
                print("\nCurrent Configuration:")
                print("-" * 50)
                print_dict(config.config)
            
            else:
                config_parser.print_help()
        
        else:
            parser.print_help()
    
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=args.verbose)
        sys.exit(1)


def print_dict(d, indent=0):
    """Pretty print dictionary."""
    for key, value in d.items():
        if isinstance(value, dict):
            print(' ' * indent + f"{key}:")
            print_dict(value, indent + 2)
        else:
            print(' ' * indent + f"{key}: {value}")


if __name__ == '__main__':
    main()
