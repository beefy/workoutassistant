import os
import time
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from datetime import datetime
import socket


app = FastAPI(title="Raspberry Pi Cluster API", version="1.0.0")


@app.get("/health")
async def health_check():
    """Health check endpoint that returns system status and cluster info."""
    hostname = socket.gethostname()
    current_time = datetime.utcnow().isoformat()
    
    return JSONResponse(
        content={
            "status": "healthy",
            "timestamp": current_time,
            "hostname": hostname,
            "service": "raspberry-pi-cluster-api",
            "version": "1.0.0"
        }
    )


def main():
    """Start the FastAPI server."""
    # Get host and port from environment variables or use defaults
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    
    print(f"Starting FastAPI server on {host}:{port}")
    
    # Run the server
    uvicorn.run(
        "tasks.rest_server:app",
        host=host,
        port=port,
        reload=False,  # Set False for production/cluster deployment
        log_level="info"
    )


if __name__ == "__main__":
    main()
