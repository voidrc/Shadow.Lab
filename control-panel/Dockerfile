ARG TAILSCALE_IMAGE_TAG=v1.84.3
FROM tailscale/tailscale:${TAILSCALE_IMAGE_TAG} AS tailscale

# Scanner tools — pinned versions for reproducibility
ARG HTTPX_VERSION=v1.6.9
ARG NUCLEI_VERSION=v3.3.7
ARG DNSX_VERSION=v1.2.2

FROM python:3.13-slim AS scanner-tools
# Install nmap and build dependencies for Go tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    nmap \
    ca-certificates \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Download pinned projectdiscovery Go tools for the container's native arch
WORKDIR /tmp/tools
RUN ARCH=$(dpkg --print-architecture) && \
    case "$ARCH" in \
        amd64) PD_ARCH="linux-amd64" ;; \
        arm64) PD_ARCH="linux-arm64" ;; \
        *) echo "Unsupported arch: $ARCH" && exit 1 ;; \
    esac && \
    wget -q "https://github.com/projectdiscovery/httpx/releases/download/${HTTPX_VERSION}/httpx_${PD_ARCH}.zip" -O httpx.zip && \
    unzip -o httpx.zip -d /usr/local/bin httpx && chmod +x /usr/local/bin/httpx && \
    wget -q "https://github.com/projectdiscovery/nuclei/releases/download/${NUCLEI_VERSION}/nuclei_${PD_ARCH}.zip" -O nuclei.zip && \
    unzip -o nuclei.zip -d /usr/local/bin nuclei && chmod +x /usr/local/bin/nuclei && \
    wget -q "https://github.com/projectdiscovery/dnsx/releases/download/${DNSX_VERSION}/dnsx_${PD_ARCH}.zip" -O dnsx.zip && \
    unzip -o dnsx.zip -d /usr/local/bin dnsx && chmod +x /usr/local/bin/dnsx && \
    rm -rf /tmp/tools

FROM python:3.13-slim

COPY --from=tailscale /usr/local/bin/tailscale /usr/local/bin/tailscale
COPY --from=scanner-tools /usr/bin/nmap /usr/bin/nmap
COPY --from=scanner-tools /usr/share/nmap /usr/share/nmap
COPY --from=scanner-tools /usr/local/bin/httpx /usr/local/bin/httpx
COPY --from=scanner-tools /usr/local/bin/nuclei /usr/local/bin/nuclei
COPY --from=scanner-tools /usr/local/bin/dnsx /usr/local/bin/dnsx
COPY --from=scanner-tools /usr/lib/python3 /usr/lib/python3
COPY --from=scanner-tools /etc/ssl/certs /etc/ssl/certs

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

RUN addgroup -S panel && adduser -S -G panel panel
USER panel

EXPOSE 8080

# Default command runs the control panel; override to run the worker:
#   docker run ... python -m app.worker
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
