FROM ollama/ollama:latest
WORKDIR /app
COPY . .
RUN pip install scikit-learn numpy
EXPOSE 8000
CMD ["python", "jarvis_main.py"]
