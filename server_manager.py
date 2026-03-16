import subprocess
import json
import requests
import socket
import logging
from pathlib import Path
from typing import Dict, Optional, List, Any
from config import SERVERS_DIR, SERVERS_CONFIG_FILE, SERVER_RAM_MIN, SERVER_RAM_MAX, MAX_SERVERS
from utils import load_servers_config, save_servers_config, is_process_running, get_server_status

logger = logging.getLogger(__name__)


class ServerManager:
    def __init__(self):
        self.servers_dir = SERVERS_DIR
        self.config_file = SERVERS_CONFIG_FILE
        self.ram_min = SERVER_RAM_MIN
        self.ram_max = SERVER_RAM_MAX
        self.max_servers = MAX_SERVERS

    def get_servers(self) -> Dict[str, Any]:
        """Get all servers from config."""
        return load_servers_config()

    def get_server_count(self) -> int:
        """Get total number of servers."""
        return len(self.get_servers())

    def get_running_count(self) -> int:
        """Get count of running servers."""
        servers = self.get_servers()
        count = 0
        for server in servers.values():
            if get_server_status(server) == 'running':
                count += 1
        return count

    def can_create_server(self) -> bool:
        """Check if we can create a new server."""
        return self.get_server_count() < self.max_servers

    def get_next_port(self) -> int:
        """Get next available port for server."""
        used_ports = set()
        servers = self.get_servers()
        for server in servers.values():
            used_ports.add(server.get('port', 25565))
        
        port = 25565
        while port in used_ports:
            port += 1
        return port

    def get_available_ip(self) -> str:
        """Get VPS public IP address."""
        try:
            response = requests.get('https://api.ipify.org', timeout=5)
            return response.text.strip()
        except Exception:
            try:
                # Fallback: try to get local IP
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
                s.close()
                return ip
            except Exception:
                return "127.0.0.1"

    def download_paper_server(self, server_path: Path) -> Optional[str]:
        """Download latest PaperMC server."""
        try:
            logger.info("Downloading PaperMC server list...")
            
            # Get latest build
            response = requests.get(
                'https://papermc.io/api/v2/projects/paper/versions',
                timeout=10
            )
            response.raise_for_status()
            versions = response.json()['versions']
            latest_version = versions[-1]
            
            # Get latest build for this version
            response = requests.get(
                f'https://papermc.io/api/v2/projects/paper/versions/{latest_version}/builds',
                timeout=10
            )
            response.raise_for_status()
            builds = response.json()['builds']
            latest_build = builds[-1]['build']
            
            # Download JAR
            jar_name = f"paper-{latest_version}-{latest_build}.jar"
            jar_url = f'https://papermc.io/api/v2/projects/paper/versions/{latest_version}/builds/{latest_build}/downloads/{jar_name}'
            
            logger.info(f"Downloading {jar_url}...")
            response = requests.get(jar_url, timeout=30)
            response.raise_for_status()
            
            jar_path = server_path / 'server.jar'
            with open(jar_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"PaperMC server downloaded: {jar_path}")
            return str(jar_path)
        except Exception as e:
            logger.error(f"Error downloading PaperMC: {e}")
            return None

    def download_vanilla_server(self, server_path: Path) -> Optional[str]:
        """Download latest Vanilla Minecraft server."""
        try:
            logger.info("Downloading Vanilla server...")
            
            # Get launcher manifest
            response = requests.get(
                'https://launcher.mojang.com/v1/objects/index.json',
                timeout=10
            )
            response.raise_for_status()
            
            manifest_url = response.json()['latest']['release']
            response = requests.get(manifest_url, timeout=10)
            response.raise_for_status()
            manifest = response.json()
            
            # Get server.jar download
            server_jar_info = manifest['downloads']['server']
            jar_url = server_jar_info['url']
            
            logger.info(f"Downloading {jar_url}...")
            response = requests.get(jar_url, timeout=30)
            response.raise_for_status()
            
            jar_path = server_path / 'server.jar'
            with open(jar_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Vanilla server downloaded: {jar_path}")
            return str(jar_path)
        except Exception as e:
            logger.error(f"Error downloading Vanilla: {e}")
            return None

    def download_spigot_server(self, server_path: Path) -> Optional[str]:
        """Download Spigot server (simplified version using pre-built)."""
        try:
            logger.info("Configuring Spigot server...")
            # Note: Full Spigot BuildTools compilation requires significant resources
            # This is a simplified version - in production, you might use pre-built jars
            logger.warning("Spigot requires BuildTools - using Paper as fallback")
            return self.download_paper_server(server_path)
        except Exception as e:
            logger.error(f"Error with Spigot: {e}")
            return None

    def create_server(self, name: str, server_type: str = 'paper') -> Optional[Dict[str, Any]]:
        """Create a new Minecraft server."""
        try:
            if not self.can_create_server():
                logger.error(f"Max servers ({self.max_servers}) reached")
                return None
            
            server_type = server_type.lower()
            if server_type not in ['paper', 'vanilla', 'spigot']:
                server_type = 'paper'
            
            # Create server directory
            server_path = self.servers_dir / name
            server_path.mkdir(exist_ok=True)
            logger.info(f"Created server directory: {server_path}")
            
            # Download server JAR
            logger.info(f"Downloading {server_type} server...")
            if server_type == 'paper':
                jar_path = self.download_paper_server(server_path)
            elif server_type == 'vanilla':
                jar_path = self.download_vanilla_server(server_path)
            else:  # spigot
                jar_path = self.download_spigot_server(server_path)
            
            if not jar_path:
                logger.error("Failed to download server JAR")
                return None
            
            # Create eula.txt
            eula_path = server_path / 'eula.txt'
            with open(eula_path, 'w') as f:
                f.write('eula=true\n')
            logger.info(f"Created EULA: {eula_path}")
            
            # Create server.properties
            properties_path = server_path / 'server.properties'
            port = self.get_next_port()
            properties_content = f'''#Minecraft server properties
level-name=world
server-port={port}
server-ip=0.0.0.0
difficulty=1
gamemode=0
max-players=20
pvp=true
spawn-protection=16
enable-command-block=true
motd=Minecraft Server
'''
            with open(properties_path, 'w') as f:
                f.write(properties_content)
            logger.info(f"Created server.properties: {properties_path}")
            
            # Create server entry in config
            servers = load_servers_config()
            servers[name] = {
                'name': name,
                'type': server_type,
                'path': str(server_path),
                'jar': jar_path,
                'pid': None,
                'status': 'stopped',
                'port': port,
                'ram_min': self.ram_min,
                'ram_max': self.ram_max,
                'created_at': str(Path(properties_path).stat().st_mtime)
            }
            save_servers_config(servers)
            logger.info(f"Server {name} created successfully")
            
            return servers[name]
        except Exception as e:
            logger.error(f"Error creating server: {e}")
            return None

    def start_server(self, name: str) -> bool:
        """Start a Minecraft server."""
        try:
            servers = load_servers_config()
            if name not in servers:
                logger.error(f"Server {name} not found")
                return False
            
            server = servers[name]
            
            if get_server_status(server) == 'running':
                logger.info(f"Server {name} is already running")
                return True
            
            server_path = Path(server['path'])
            jar_file = server['jar']
            
            if not Path(jar_file).exists():
                logger.error(f"JAR file not found: {jar_file}")
                return False
            
            # Start server process
            cmd = [
                'java',
                f'-Xms{server["ram_min"]}',
                f'-Xmx{server["ram_max"]}',
                '-jar',
                jar_file,
                'nogui'
            ]
            
            process = subprocess.Popen(
                cmd,
                cwd=str(server_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            server['pid'] = process.pid
            server['status'] = 'running'
            servers[name] = server
            save_servers_config(servers)
            
            logger.info(f"Server {name} started with PID {process.pid}")
            return True
        except Exception as e:
            logger.error(f"Error starting server {name}: {e}")
            return False

    def stop_server(self, name: str) -> bool:
        """Stop a Minecraft server."""
        try:
            servers = load_servers_config()
            if name not in servers:
                logger.error(f"Server {name} not found")
                return False
            
            server = servers[name]
            pid = server.get('pid')
            
            if not pid or not is_process_running(pid):
                server['status'] = 'stopped'
                server['pid'] = None
                servers[name] = server
                save_servers_config(servers)
                logger.info(f"Server {name} is already stopped")
                return True
            
            # Try graceful shutdown
            try:
                process = subprocess.Popen(
                    ['kill', '-TERM', str(pid)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                process.wait(timeout=30)
            except Exception:
                # Force kill if graceful shutdown fails
                subprocess.run(['kill', '-9', str(pid)], stdout=subprocess.DEVNULL)
            
            server['status'] = 'stopped'
            server['pid'] = None
            servers[name] = server
            save_servers_config(servers)
            
            logger.info(f"Server {name} stopped")
            return True
        except Exception as e:
            logger.error(f"Error stopping server {name}: {e}")
            return False

    def restart_server(self, name: str) -> bool:
        """Restart a Minecraft server."""
        try:
            if self.stop_server(name):
                import time
                time.sleep(2)
                return self.start_server(name)
            return False
        except Exception as e:
            logger.error(f"Error restarting server {name}: {e}")
            return False

    def delete_server(self, name: str) -> bool:
        """Delete a Minecraft server."""
        try:
            servers = load_servers_config()
            if name not in servers:
                logger.error(f"Server {name} not found")
                return False
            
            server = servers[name]
            
            # Stop server first
            if get_server_status(server) == 'running':
                self.stop_server(name)
            
            # Delete server directory
            import shutil
            server_path = Path(server['path'])
            if server_path.exists():
                shutil.rmtree(server_path)
                logger.info(f"Deleted server directory: {server_path}")
            
            # Remove from config
            del servers[name]
            save_servers_config(servers)
            
            logger.info(f"Server {name} deleted")
            return True
        except Exception as e:
            logger.error(f"Error deleting server {name}: {e}")
            return False

    def get_server_logs(self, name: str, lines: int = 20) -> str:
        """Get server logs (last N lines)."""
        try:
            servers = load_servers_config()
            if name not in servers:
                return "Server not found"
            
            server = servers[name]
            log_file = Path(server['path']) / 'logs' / 'latest.log'
            
            if not log_file.exists():
                return "No logs available yet"
            
            with open(log_file, 'r', errors='ignore') as f:
                log_lines = f.readlines()
            
            # Get last N lines
            recent_logs = log_lines[-lines:]
            return ''.join(recent_logs)
        except Exception as e:
            logger.error(f"Error getting logs for {name}: {e}")
            return f"Error reading logs: {e}"
