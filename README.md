# workoutassistant

An LLM that will answer emails

### Setup Local LLM

```
# Create models directory
mkdir -p ~/models
cd ~/models

# Download Phi-3-mini (~2.4GB)
wget https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf
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

### Run the script

Start it in the background
```
nohup python src/main.py > output.log 2>&1 &
```

Find the process to kill it when done
```
# Find by script name
ps aux | grep src/main.py
```

Kill the process
```
# Kill by PID
kill 12345

# Force kill
kill -9 12345
```
