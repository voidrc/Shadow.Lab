ARG TAILSCALE_IMAGE_TAG=v1.84.3
FROM tailscale/tailscale:${TAILSCALE_IMAGE_TAG} AS tailscale
FROM python:3.13.7-alpine3.22

COPY --from=tailscale /usr/local/bin/tailscale /usr/local/bin/tailscale

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN addgroup -S panel && adduser -S -G panel panel
USER panel

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
