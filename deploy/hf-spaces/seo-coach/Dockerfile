FROM python:3.11

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pin Gradio 5.x — code uses type="messages" and Blocks(css=) which break in Gradio 6
RUN pip install --no-cache-dir --upgrade 'gradio>=5.0.0,<6.0.0'

# Install HF Spaces specific packages (without downgrading gradio)
RUN pip install --no-cache-dir 'uvicorn>=0.14.0' spaces

# Copy application code
COPY . .

# Expose port
EXPOSE 7860

# Set environment variables
ENV GRADIO_SERVER_NAME="0.0.0.0"
ENV GRADIO_SERVER_PORT="7860"

# Run the application
CMD ["python", "app.py"]
