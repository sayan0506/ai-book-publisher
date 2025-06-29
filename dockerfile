# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8080
ENV PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip first
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install packages individually to avoid conflicts and speed up builds
# Core dependencies first
RUN pip install --no-cache-dir protobuf==3.20.3
RUN pip install --no-cache-dir python-dotenv==1.1.1
RUN pip install --no-cache-dir beautifulsoup4==4.13.4

# Google Cloud packages
RUN pip install --no-cache-dir google-auth==2.34.0
RUN pip install --no-cache-dir google-cloud-storage==2.18.0
RUN pip install --no-cache-dir google-cloud-logging
RUN pip install --no-cache-dir google-generativeai

# Lightweight packages
RUN pip install --no-cache-dir graphviz==0.21
RUN pip install --no-cache-dir Pillow==11.2.1

# Streamlit
RUN pip install --no-cache-dir streamlit==1.46.0

# LangChain packages
RUN pip install --no-cache-dir langchain_core==0.3.66
RUN pip install --no-cache-dir langchain_google_vertexai==2.0.26
RUN pip install --no-cache-dir langgraph==0.4.8

# ChromaDB - use lighter version to avoid OpenTelemetry conflicts
RUN pip install --no-cache-dir chromadb==1.0.13


# Playwright - install without browsers to save time and space
RUN pip install --no-cache-dir playwright==1.52.0
RUN playwright install chromium
# needed as docker container doesnt have gui support thus it needs playwright deps for docker 
RUN playwright install-deps

# Note: Not running 'playwright install' to avoid downloading browser binaries

# Copy application code
COPY . .

RUN ls -la
# Debug: List Python files and check imports
RUN ls -la /app/
RUN python -c "import sys; print('Python path:', sys.path)"
RUN python -c "import os; print('Files in /app:', os.listdir('/app'))"

# Debug: Check if book_workflow.py exists and its contents
RUN if [ -f "book_workflow.py" ]; then echo "book_workflow.py exists"; else echo "book_workflow.py NOT FOUND"; fi
RUN if [ -f "book_workflow.py" ]; then head -20 book_workflow.py; fi


# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/temp

# Expose port
#EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/_stcore/health || exit 1

# Run the application
CMD streamlit run main.py \
    --server.port=$PORT \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.fileWatcherType=none \
    --browser.gatherUsageStats=false