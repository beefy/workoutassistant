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

## 🐳 Docker Deployment (Recommended)

The easiest way to deploy WorkoutAssistant is using Docker. This provides:
- ✅ Automatic updates when new versions are released
- ✅ Automatic restart on failures
- ✅ Auto-startup when Raspberry Pi restarts using a Docker container with watchtower for automatic updates when a new image is pushed to DockerHub
- ✅ Proper secret management
- ✅ Consistent environment across different systems

### Quick Start

1. **Create your secrets file** (📋 **CRITICAL STEP**)
   ```bash
   # Create the secrets file that will be mounted into the container
   nano ~/.variables
   ```
   
   Add your environment variables (replace with your actual values):
   ```bash
   GMAIL_ADDRESS=your-email@gmail.com
   GMAIL_APP_PASSWORD=your-app-password
   TEST_EMAIL=test@example.com
   ADMIN_EMAIL=admin@example.com
   APPROVED_PHRASE="your approval phrase"
   MOLTBOOK_API_KEY=your-api-key
   TRACKING_API_USERNAME=your-username
   TRACKING_API_PASSWORD=your-password
   SOLANA_ADDRESS=your-wallet-address
   SOLANA_PRIVATE_KEY=your-private-key
   JUPITER_API_KEY=your-jupiter-key
   BIRDEYE_API_KEY=your-birdeye-key
   ```

2. **Run the automated deployment script**
   ```bash
   curl -sSL https://raw.githubusercontent.com/YOUR_USERNAME/workoutassistant/main/deploy.sh | bash
   ```

   Or manually:
   ```bash
   wget https://raw.githubusercontent.com/YOUR_USERNAME/workoutassistant/main/deploy.sh
   chmod +x deploy.sh
   ./deploy.sh
   ```

3. **That's it!** 🎉 The container will:
   - Download and start automatically
   - Download required AI models (this may take a while on first start)
   - Set up auto-restart on failures
   - Set up auto-startup on system boot
   - Check for updates every 5 minutes and auto-update

### Manual Docker Setup

If you prefer manual setup:

```bash
# Create directories
mkdir -p ~/workoutassistant/{data,models,logs}
cd ~/workoutassistant

# Download docker-compose.yml
curl -O https://raw.githubusercontent.com/YOUR_USERNAME/workoutassistant/main/docker-compose.yml

# Make sure your ~/.variables file exists with secrets
# Then start the containers
docker compose up -d
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

### � Setting Up CI/CD (For Developers)

To set up automatic Docker image building and publishing:

1. **Fork this repository** to your GitHub account

2. **Set up DockerHub account** and create a repository named `workoutassistant`

3. **Run the configuration script** to update usernames automatically:
   ```bash
   ./setup-config.sh
   ```
   This will prompt you for your GitHub and DockerHub usernames and update all configuration files automatically.

4. **Configure GitHub Secrets** in your repository settings:
   - Go to Settings → Secrets and variables → Actions
   - Add these repository secrets:
     - `DOCKERHUB_USERNAME`: Your DockerHub username
     - `DOCKERHUB_TOKEN`: Your DockerHub access token ([create one here](https://hub.docker.com/settings/security))

5. **Commit and push** to main branch:
   ```bash
   git add .
   git commit -m "Configure usernames for deployment"
   git push origin main
   ```
   
   GitHub Actions will automatically build and push the Docker image!

### 🔒 Security & Secret Management

- **Secrets are NEVER included in the Docker image**
- All sensitive data is loaded from `~/.variables` file on your Pi
- The image is safe to be public on DockerHub
- Environment variables are only mounted at runtime
- The `.dockerignore` file ensures no local secrets are accidentally included

### 🏥 Health Monitoring

The container includes health checks that monitor if the main process is running. Container will restart automatically if health checks fail.

### 📊 System Status

Use the included status script to check if everything is working properly:

```bash
# Download and run the status checker
curl -sSL https://raw.githubusercontent.com/YOUR_USERNAME/workoutassistant/main/status.sh | bash

# Or if you have the repo cloned
./status.sh
```

### 🔧 Troubleshooting

**Container won't start:**
- Check if `~/.variables` file exists and has the required variables
- Verify Docker is running: `sudo systemctl status docker`
- Check logs: `docker compose logs workoutassistant`

**Auto-updates not working:**
- Ensure Watchtower container is running: `docker compose ps`
- Check Watchtower logs: `docker compose logs watchtower`

**Email notifications not working:**
- Verify Gmail credentials in `~/.variables`
- Check if 2FA is enabled and App Password is generated
- Test manually: `docker compose exec workoutassistant python src/scripts/test_email.py`

### 📜 Included Scripts

The repository includes several helpful scripts:

- **`setup-config.sh`** - Automatically configure GitHub/DockerHub usernames in all files
- **`deploy.sh`** - One-click deployment script for Raspberry Pi
- **`status.sh`** - System status checker and diagnostics
- **`.variables.example`** - Template for environment variables

## 💻 Manual Installation (Alternative)

If you prefer not to use Docker, you can install manually:

## 💻 Manual Installation (Alternative)

If you prefer not to use Docker, you can install manually:

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
