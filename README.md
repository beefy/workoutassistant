# workoutassistant

An LLM that will answer emails

### Setup Local LLM

```
# Create models directory
mkdir -p ~/models
cd ~/models

# Download Phi-3-mini (~2.4GB)
wget https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf

# Or the 128k version
wget https://huggingface.co/microsoft/Phi-3-mini-128k-instruct-gguf/resolve/main/Phi-3-mini-128k-instruct-q4.gguf
```

### SQLite Database Setup

SQLite comes pre-installed on most systems. To verify:

```bash
# Check if SQLite is installed
sqlite3 --version

# If not installed:
# Ubuntu/Debian:
sudo apt-get install sqlite3

# macOS (if not present):
brew install sqlite

# CentOS/RHEL:
sudo yum install sqlite
```

Create the initial tables
```
PYTHONPATH=src python src/create_tables.py
```

### Email setup

1. Create a gmail account for this project
2. Enable 2FA
3. Generate an App Password: https://myaccount.google.com/apppasswords

Store the necessary environment variables
```
export GMAIL_ADDRESS=<email@gmail.com>
export GMAIL_APP_PASSWORD=<app_password>
export TEST_EMAIL=<emailtosendtestemailto@gmail.com>
export ADMIN_EMAIL=<adminemail@gmail.com>
export APPROVED_PHRASE=<phrase to add to approve list>
```

### Moltbook setup
```
curl -X POST https://www.moltbook.com/api/v1/agents/register \
  -H "Content-Type: application/json" \
  -d '{"name": "YourAgentName", "description": "What you do"}'
```

```
export MOLTBOOK_API_KEY=<api_key>
```

### Run the script

Start it in the background
```
# Use -u flag for unbuffered output and full path for log file
nohup python -u src/main.py > $(pwd)/output.log 2>&1 &

# Alternative: Set PYTHONUNBUFFERED environment variable
nohup env PYTHONUNBUFFERED=1 python src/main.py > $(pwd)/output.log 2>&1 &
```

Find the process to kill it when done
```
# Find by script name
ps aux | grep src/main.py
```

Monitor the output in real-time
```
# Follow the log file continuously (Ctrl+C to stop)
tail -f output.log

# Alternative: Show last 50 lines then follow
tail -n 50 -f output.log

# Less command with follow mode (F key to follow, q to quit)
less +F output.log
```

Kill the process
```
# Kill by PID
kill 12345

# Force kill
kill -9 12345
```
