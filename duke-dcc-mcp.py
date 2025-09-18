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

#Update these with your own credentials
username = None
ssh_key_path = None


class ConnectionParams(BaseModel):
    hostname: str = Field(default="dcc-login.oit.duke.edu", description="DCC hostname")
    username: Optional[str] = Field(default=username, description="Duke NetID")
    key_path: Optional[str] = Field(default=ssh_key_path, description="Path to SSH private key")

class FileOperation(BaseModel):
    path: str = Field(description="File or directory path")
    detailed: bool = Field(default=False, description="Show detailed information")

class MoveOperation(BaseModel):
    source: str = Field(description="Source path")
    destination: str = Field(description="Destination path")

class OrganizeParams(BaseModel):
    path: str = Field(description="Directory to organize")
    method: str = Field(default="type", description="Organization method: type, date, or size")
    create_subdirs: bool = Field(default=True, description="Create subdirectories for organization")

class CommandParams(BaseModel):
    command: str = Field(description="Shell command to execute")

def ensure_connected():
    """Ensure SSH connection is established"""
    global connected, ssh_client
    if not connected or not ssh_client:
        raise Exception("Not connected to DCC. Use connect_to_dcc tool first.")

def format_file_info(filepath: str, stat_info, detailed: bool = False):
    """Format file information for display"""
    is_dir = stat.S_ISDIR(stat_info.st_mode)
    file_type = "directory" if is_dir else "file"
    
    if detailed:
        mod_time = datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        permissions = stat.filemode(stat_info.st_mode)
        size = stat_info.st_size if not is_dir else "-"
        
        return {
            "name": os.path.basename(filepath),
            "type": file_type,
            "size": size,
            "permissions": permissions,
            "modified": mod_time,
            "path": filepath
        }
    else:
        return {
            "name": os.path.basename(filepath),
            "type": file_type,
            "path": filepath
        }

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
        passphrase = "Grill"
        
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
def list_files(params: FileOperation) -> Dict[str, Any]:
    """List files and directories in a remote path"""
    ensure_connected()
    
    try:
        files = []
        file_list = sftp_client.listdir_attr(params.path)
        
        for file_attr in file_list:
            filepath = os.path.join(params.path, file_attr.filename)
            file_info = format_file_info(filepath, file_attr, params.detailed)
            files.append(file_info)
        
        return {
            "status": "success",
            "path": params.path,
            "files": files,
            "count": len(files)
        }
        
    except Exception as e:
        return {"status": "error", "message": f"Failed to list files: {str(e)}"}

@mcp.tool()
def create_directory(path: str, recursive: bool = False) -> Dict[str, Any]:
    """Create a directory on the remote server"""
    ensure_connected()
    
    try:
        if recursive:
            # Create parent directories if needed
            sftp_client.makedirs(path)
        else:
            sftp_client.mkdir(path)
        
        return {"status": "success", "message": f"Directory created: {path}"}
        
    except Exception as e:
        return {"status": "error", "message": f"Failed to create directory: {str(e)}"}

@mcp.tool()
def move_file(params: MoveOperation) -> Dict[str, Any]:
    """Move or rename a file/directory on the remote server"""
    ensure_connected()
    
    try:
        # Use SSH command for more reliable move operation
        stdin, stdout, stderr = ssh_client.exec_command(f"mv '{params.source}' '{params.destination}'")
        stderr_output = stderr.read().decode()
        
        if stderr_output:
            return {"status": "error", "message": f"Move failed: {stderr_output}"}
        
        return {"status": "success", "message": f"Moved {params.source} to {params.destination}"}
        
    except Exception as e:
        return {"status": "error", "message": f"Failed to move file: {str(e)}"}

@mcp.tool()
def copy_file(params: MoveOperation) -> Dict[str, Any]:
    """Copy a file on the remote server"""
    ensure_connected()
    
    try:
        # Use SSH command for copy operation
        stdin, stdout, stderr = ssh_client.exec_command(f"cp -r '{params.source}' '{params.destination}'")
        stderr_output = stderr.read().decode()
        
        if stderr_output:
            return {"status": "error", "message": f"Copy failed: {stderr_output}"}
        
        return {"status": "success", "message": f"Copied {params.source} to {params.destination}"}
        
    except Exception as e:
        return {"status": "error", "message": f"Failed to copy file: {str(e)}"}

@mcp.tool()
def delete_file(path: str, recursive: bool = False) -> Dict[str, Any]:
    """Delete a file or directory on the remote server"""
    ensure_connected()
    
    try:
        # Check if it's a directory
        try:
            stat_info = sftp_client.stat(path)
            is_dir = stat.S_ISDIR(stat_info.st_mode)
        except:
            is_dir = False
        
        if is_dir:
            if recursive:
                # Use SSH command for recursive deletion
                stdin, stdout, stderr = ssh_client.exec_command(f"rm -rf '{path}'")
                stderr_output = stderr.read().decode()
                if stderr_output:
                    return {"status": "error", "message": f"Delete failed: {stderr_output}"}
            else:
                sftp_client.rmdir(path)
        else:
            sftp_client.remove(path)
        
        return {"status": "success", "message": f"Deleted: {path}"}
        
    except Exception as e:
        return {"status": "error", "message": f"Failed to delete: {str(e)}"}

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
def get_file_info(path: str) -> Dict[str, Any]:
    """Get detailed information about a file or directory"""
    ensure_connected()
    
    try:
        stat_info = sftp_client.stat(path)
        file_info = format_file_info(path, stat_info, detailed=True)
        
        return {"status": "success", "file_info": file_info}
        
    except Exception as e:
        return {"status": "error", "message": f"Failed to get file info: {str(e)}"}

@mcp.tool()
def organize_files(params: OrganizeParams) -> Dict[str, Any]:
    """Organize files in a directory by type, date, or size"""
    ensure_connected()
    
    try:
        # List files in the directory
        file_list = sftp_client.listdir_attr(params.path)
        organized_count = 0
        
        for file_attr in file_list:
            filepath = os.path.join(params.path, file_attr.filename)
            
            # Skip directories unless organizing by date
            if stat.S_ISDIR(file_attr.st_mode) and params.method != "date":
                continue
            
            # Determine organization folder
            if params.method == "type":
                ext = os.path.splitext(file_attr.filename)[1].lower()
                if ext:
                    folder_name = f"{ext[1:]}_files"  # Remove the dot
                else:
                    folder_name = "no_extension"
            elif params.method == "date":
                mod_date = datetime.fromtimestamp(file_attr.st_mtime)
                folder_name = mod_date.strftime("%Y-%m")
            elif params.method == "size":
                size = file_attr.st_size
                if size < 1024 * 1024:  # < 1MB
                    folder_name = "small_files"
                elif size < 100 * 1024 * 1024:  # < 100MB
                    folder_name = "medium_files"
                else:
                    folder_name = "large_files"
            
            if params.create_subdirs:
                # Create subdirectory if it doesn't exist
                subdir_path = os.path.join(params.path, folder_name)
                try:
                    sftp_client.mkdir(subdir_path)
                except:
                    pass  # Directory might already exist
                
                # Move file to subdirectory
                new_path = os.path.join(subdir_path, file_attr.filename)
                stdin, stdout, stderr = ssh_client.exec_command(f"mv '{filepath}' '{new_path}'")
                
                if not stderr.read().decode():
                    organized_count += 1
        
        return {
            "status": "success",
            "message": f"Organized {organized_count} files by {params.method}",
            "organized_count": organized_count
        }
        
    except Exception as e:
        return {"status": "error", "message": f"Failed to organize files: {str(e)}"}

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