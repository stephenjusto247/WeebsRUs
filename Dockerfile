FROM python:3.10.13-slim AS compiler
# Disable buffering behavior
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Run and enable virtual env
RUN python -m venv venv
ENV PATH="/app/venv/bin:$PATH"

# Copy and install dependencies
COPY ./requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

FROM python:3.10.13-slim AS runner

WORKDIR /app

# Copy virtual environment contents & enable virtual env
COPY --from=compiler /app/venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Install ffmpeg
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

# Copy application code
COPY . /app

CMD ["python", "bot.py"]
