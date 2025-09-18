# Duke Computing Cluster Manager (MCP Server)

An **MCP-powered application** to facilitate **remote management** of the  
**Duke Computing Cluster (DCC)** via SSH.  

Built with:
- **Remote Execution:** [`paramiko`](https://www.paramiko.org/)  
- **Orchestration:** [FastMCP](https://github.com/modelcontextprotocol/servers)  
- **Validation:** [Pydantic](https://docs.pydantic.dev/)  

---

## 🚀 Features
- **SSH Management** – connect to the Duke Computing Cluster using your Duke NetID + SSH key.  
- **File Transfer** – upload and download files between your machine and the cluster.  
- **Remote Command Execution** – run shell commands and collect outputs.  
- **Session Handling** – disconnect and clean up connections safely.  

---

## 🧩 MCP Tools

### 🔑 `connect_to_dcc`
- Connects to the DCC login node (`dcc-login.oit.duke.edu` by default).  
- Uses Duke NetID + SSH private key authentication.  
- Returns a success or failure message.  

### 📤 `upload_file`
- Uploads a file from your **local machine → cluster**.  
- Example: `upload_file("./data/input.txt", "/home/<netid>/input.txt")`.  

### 📥 `download_file`
- Downloads a file from the **cluster → local machine**.  
- Example: `download_file("/home/<netid>/results.txt", "./results/output.txt")`.  

### 🖥️ `execute_command`
- Runs a shell command on the cluster.  
- Returns: `stdout`, `stderr`, and `exit_code`.  
- Example:  
  ```json
  {
    "command": "ls -l",
    "stdout": "...",
    "stderr": "",
    "exit_code": 0
  }


## ⚙️ Installation

### 📦 Using `environment.yml`

You can create a conda environment from the provided `environment.yml` file to ensure all dependencies are installed correctly.

**Create the environment:**

conda env create -f environment.yml
Activate the environment:

bash
Copy code
conda activate dcc-mcp
(Replace dcc-mcp with the environment name defined in environment.yml if different.)

Verify installation:

bash
Copy code
conda list
▶️ Running the MCP Server
Start the MCP server:

bash
Copy code
python dcc_manager.py
This launches the FastMCP server and exposes the cluster management tools.

⚠️ Notes
Ensure your SSH key is registered with the DCC and the path matches your config.

The script currently expects a private key passphrase ("Grill" placeholder) – change this for your setup.

Always call disconnect after work to close sessions cleanly.

🛠️ Tech Stack
FastMCP – MCP tool orchestration

Paramiko – SSH + SFTP

Pydantic – parameter validation

Python Standard Library – asyncio, pathlib, datetime, etc.
