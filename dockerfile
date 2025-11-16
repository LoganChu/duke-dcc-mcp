FROM python:3.11-slim

WORKDIR /app

# Copy environment file and install dependencies
COPY .env* ./
COPY environment.yml ./
# If using conda/mamba:
# RUN conda env create -f environment.yml
# Or if using pip with requirements.txt instead:
# COPY requirements.txt ./
# RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY *.py ./
COPY ui.py ./

# Expose port if your app serves HTTP
EXPOSE 8000

# Run the application
CMD ["python", "duke-dcc-mcp.py"]