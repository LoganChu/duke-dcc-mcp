#!/usr/bin/env python3

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional
from pathlib import Path
import paramiko
from getpass import getpass
import stat
import os
from datetime import datetime
import shutil

# FastMCP imports
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

# Initialize FastMCP
mcp = FastMCP("Duke Computing Cluster Manager")

# Global SSH connection variables
ssh_client = None
sftp_client = None
connected = False

username = None
ssh_key = None
ssh_passphrase = None

class ConnectionParams(BaseModel):
    hostname: str = Field(default="dcc-login.oit.duke.edu", description="DCC hostname")
    username: Optional[str] = Field(default=username, description="Duke NetID")
    key_path: Optional[str] = Field(default=ssh_key, description="Path to SSH private key")

class CommandParams(BaseModel):
    command: str = Field(description="Shell command to execute")

def ensure_connected():
    """Ensure SSH connection is established"""
    global connected, ssh_client
    if not connected or not ssh_client:
        raise Exception("Not connected to DCC. Use connect_to_dcc tool first.")

@mcp.tool()
def connect_to_dcc(params: ConnectionParams) -> Dict[str, Any]:
    """Connect to Duke Computing Cluster via SSH"""
    global ssh_client, sftp_client, connected
    
    try:
        username = params.username
        if not username:
            username = input("Enter Duke NetID: ")
        
        key_path = params.key_path
        if not key_path:
            key_path = input("Enter SSH key path")
        
        # Get passphrase for key
        passphrase = ssh_passphrase
        
        key = paramiko.RSAKey.from_private_key_file(str(key_path), password=passphrase)
        
        # Create SSH client
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Connect
        ssh_client.connect(params.hostname, username=username, pkey=key)
        sftp_client = ssh_client.open_sftp()
        connected = True
        
        return {"status": "success", "message": f"Connected to {params.hostname} as {username}"}
        
    except Exception as e:
        return {"status": "error", "message": f"Connection failed: {str(e)}"}

@mcp.tool()
def upload_file(local_path: str, remote_path: str) -> Dict[str, Any]:
    """Upload a file from local machine to remote server"""
    ensure_connected()
    
    try:
        local_file = Path(local_path)
        if not local_file.exists():
            return {"status": "error", "message": f"Local file not found: {local_path}"}
        
        sftp_client.put(local_path, remote_path)
        return {"status": "success", "message": f"Uploaded {local_path} to {remote_path}"}
        
    except Exception as e:
        return {"status": "error", "message": f"Failed to upload: {str(e)}"}

@mcp.tool()
def download_file(remote_path: str, local_path: str) -> Dict[str, Any]:
    """Download a file from remote server to local machine"""
    ensure_connected()
    
    try:
        # Create local directory if it doesn't exist
        local_file = Path(local_path)
        local_file.parent.mkdir(parents=True, exist_ok=True)
        
        sftp_client.get(remote_path, local_path)
        return {"status": "success", "message": f"Downloaded {remote_path} to {local_path}"}
        
    except Exception as e:
        return {"status": "error", "message": f"Failed to download: {str(e)}"}

@mcp.tool()
def execute_command(params: CommandParams) -> Dict[str, Any]:
    """Execute a command on the remote server"""
    ensure_connected()
    
    try:
        stdin, stdout, stderr = ssh_client.exec_command(params.command)
        
        stdout_output = stdout.read().decode()
        stderr_output = stderr.read().decode()
        exit_code = stdout.channel.recv_exit_status()
        
        return {
            "status": "success",
            "command": params.command,
            "stdout": stdout_output,
            "stderr": stderr_output,
            "exit_code": exit_code
        }
        
    except Exception as e:
        return {"status": "error", "message": f"Failed to execute command: {str(e)}"}

@mcp.tool()
def disconnect() -> Dict[str, Any]:
    """Disconnect from the DCC server"""
    global ssh_client, sftp_client, connected
    
    try:
        if sftp_client:
            sftp_client.close()
        if ssh_client:
            ssh_client.close()
        
        connected = False
        ssh_client = None
        sftp_client = None
        
        return {"status": "success", "message": "Disconnected from DCC"}
        
    except Exception as e:
        return {"status": "error", "message": f"Error during disconnect: {str(e)}"}

if __name__ == "__main__":
    # Run the FastMCP server
    mcp.run()