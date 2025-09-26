FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir pynacl
COPY tools/verifier/offline_verify.py /app/offline_verify.py
COPY tools/verifier/tuf/ /app/tuf/
ENTRYPOINT ["python3", "/app/offline_verify.py"]