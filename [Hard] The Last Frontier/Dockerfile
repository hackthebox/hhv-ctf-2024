FROM python:3.9-slim

RUN apt-get update
RUN apt-get install -y supervisor

# Setup app
RUN mkdir -p /app

# Copy challenge
COPY challenge/ /app


# Setup supervisor
COPY config/supervisord.conf /etc/supervisord.conf

# Expose the port the challenge is reachable on
EXPOSE 1337


# Expose the port the challenge is reachable on
EXPOSE 1338

# Run supervisord
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisord.conf"]
