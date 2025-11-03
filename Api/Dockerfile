# Use a Python base image, which is much cleaner and smaller than Ubuntu for Python apps
FROM python:3.10-slim 

# 1. Set the working directory
WORKDIR /app

# 2. Install Flask using the Python package installer (pip)
#    It's best practice to use a requirements.txt file, but for a single package:
RUN pip install flask flask-cors

# 3. Copy the application code
COPY app.py .
COPY templates/ templates/

# 4. Expose the port
EXPOSE 5000

# 5. Define the command to run the application
CMD ["python3", "app.py"]