# workoutassistant

An LLM that will answer emails. Capable of running on a raspberry pi with 6gb of RAM.

 - Email uses gmail SMTP/IMAP
 - LLM uses phi-3-mini and runs locally
 - Image captioning uses blip and runs locally
 - Image generation runs in the cloud using a hugging face interface (free)
 - Image to image (image editing) runs in the cloud using a hugging face interface ($0.02 to $0.03 per call) 
 - Approve List for approved email senders is stored in SQLite
 - Web search uses duck duck go

Tasks that run on a regular schedule:

 - Heartbeat
 - Check and process emails
 - Create and send a daily newsletter based on the front page news of apnews.com
 - Browse Moltbook, making posts, making comments, or upvoting/downvoting posts
 - Trade cryptocurrency on the Solana blockchain based on 5 indicators from the last 72 hours of price data

### Environment Variables

See `.variables.example` for expected environment variables.

You also need a `.variables-watchtower` for watchtower variables (used to send email alerts on server restart or failures)
```
GMAIL_APP_PASSWORD=your_app_password_here
GMAIL_ADDRESS=your_email@gmail.com
ADMIN_EMAIL=admin@example.com
```

### Docker Commands

```bash
# View logs
docker compose logs -f workoutassistant

# Check status
docker compose ps

# Update to latest version
docker compose pull && docker compose up -d

# Stop containers
docker compose down

# Restart
docker compose restart
```

### 🔄 Automatic Updates

The deployment includes [Watchtower](https://github.com/containrrr/watchtower) which:
- Polls DockerHub every 5 minutes for new images
- Automatically pulls and deploys updates
- Sends email notifications when updates occur
- Cleans up old images to save space

Updates are triggered automatically when code is pushed to the main branch via GitHub Actions.

### Setting Up CI/CD

To set up automatic Docker image building and publishing:

**Set up DockerHub account** and create a repository named `workoutassistant`

**Configure GitHub Secrets** in your repository settings:
   - Go to Settings → Secrets and variables → Actions
   - Add these repository secrets:
     - `DOCKERHUB_USERNAME`: Your DockerHub username
     - `DOCKERHUB_TOKEN`: Your DockerHub access token ([create one here](https://hub.docker.com/settings/security))

### 🏥 Health Monitoring

The container includes health checks that monitor if the main process is running. Container will restart automatically if health checks fail.

### 🔧 Troubleshooting

**Container won't start:**
- Check if `~/.variables` file exists and has the required variables
- Verify Docker is running: `sudo systemctl status docker`
- Check logs: `docker compose logs workoutassistant`

**Auto-updates not working:**
- Ensure Watchtower container is running: `docker compose ps`
- Check Watchtower logs: `docker compose logs watchtower`

### Prerequisites

Install system dependencies:
```bash
# Headless web search
sudo apt install -y chromium chromium-driver

# Python and pip (usually pre-installed)
sudo apt install -y python3 python3-pip

# SQLite (usually pre-installed)
sudo apt install -y sqlite3
```

### Install Python Dependencies

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/workoutassistant.git
cd workoutassistant

# Install Python packages
pip install -r requirements.txt
```

### Setup Local LLM

```
# Create models directory
mkdir -p ~/models
cd ~/models

# Download Phi-3-mini 4k version (~2.4GB)
wget https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf

# Download Phi-3-mini 128k version for longer context windows
wget https://huggingface.co/mradermacher/Phi-3-mini-128k-instruct-ft-i1-GGUF/resolve/main/Phi-3-mini-128k-instruct-ft.i1-Q4_K_M.gguf?download=true
```

You may need to create a hugging face user and browse the web UI for models: https://huggingface.co/docs/huggingface_hub/v1.4.0/quick-start#authentication

### Local Image Captioning Setup

The image captioning module automatically downloads the BLIP-base model (~1.2GB) on first use. For manual installation:

```bash
# Install required packages
pip install torch transformers pillow

# Test the image captioning (will auto-download model)
python src/image_captioning.py
```

**Model Details:**
- **Model**: Salesforce BLIP-base (blip-image-captioning-base)
- **Size**: ~1.2GB download
- **RAM Usage**: ~2-3GB during inference
- **Performance**: 10-30 seconds per image on Raspberry Pi, 2-5 seconds on desktop CPU
- **Capabilities**: Image captioning and visual question answering

**Raspberry Pi Optimization:**
- Uses CPU-only inference (no GPU required)
- Optimized for low memory usage with `low_cpu_mem_usage=True`
- Automatically detected Pi hardware for performance messaging

**Usage Example:**
```python
from src.image_captioning import caption_image_local, ask_about_image_local

# Basic image captioning
caption = caption_image_local('path/to/image.jpg')
print(f"Caption: {caption}")

# Visual question answering
answer = ask_about_image_local('path/to/image.jpg', 'What colors are in this image?')
print(f"Answer: {answer}")
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
PYTHONPATH=src python src/scripts/create_tables.py
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

### API integration for tracking status
```
export TRACKING_API_USERNAME=<username>
export TRACKING_API_PASSWORD=<password>
```

Create account
```
python src/scripts/register_tracking_api.py
```

### Crypto Setup

Create crypto wallets
```
python src/scripts/create_crypto_wallets.py
```

Acquire and set these environment variables
```
export SOLANA_ADDRESS=<wallet to trade from>
export SOLANA_PRIVATE_KEY=<base 58 private key for wallet>
export JUPITER_API_KEY=<api key for getting trade info>
export BIRDEYE_API_KEY=<api key for getting price data>
```

Check crypto balance
```
python src/scripts/get_crypto_balance.py
```

### Lichess Setup
Create a new account on Lichess. Convert it to a bot account with this curl command. Note: the account cannot have any games played.
```
curl -d '' https://lichess.org/api/bot/account/upgrade -H "Authorization: Bearer <your api token>"
{"ok":true}
```

### Youtube / Discord Setup
```
brew install ffmpeg
```
See DISCORD_BOT_README.md

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
