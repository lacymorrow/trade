# Use Node.js base image with specific version
FROM node:18 AS builder

# Set working directory
WORKDIR /app

# Install Python and dependencies
RUN apt-get update && apt-get install -y \
	python3 \
	python3-pip \
	python3-venv \
	build-essential \
	python3-dev \
	ca-certificates \
	openssl \
	&& rm -rf /var/lib/apt/lists/*

# Update certificates
RUN update-ca-certificates

# Install pnpm globally
RUN npm install -g pnpm@latest

# Copy package files
COPY package*.json pnpm-lock.yaml ./
COPY requirements.txt ./

# Create and activate virtual environment
RUN python3 -m venv /venv
ENV PATH="/venv/bin:$PATH"
ENV PYTHONPATH="/venv/lib/python3.12/site-packages"
ENV SSL_CERT_FILE="/etc/ssl/certs/ca-certificates.crt"
ENV REQUESTS_CA_BUNDLE="/etc/ssl/certs/ca-certificates.crt"
ENV PIP_CERT="/etc/ssl/certs/ca-certificates.crt"

# Install dependencies
RUN pnpm install --frozen-lockfile

# Install Python dependencies with SSL verification disabled (only for build)
RUN pip3 install --upgrade pip --trusted-host pypi.org --trusted-host files.pythonhosted.org && \
	pip3 install wheel setuptools --trusted-host pypi.org --trusted-host files.pythonhosted.org && \
	pip3 install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org

# Copy source code
COPY . .

# Build Next.js app
RUN pnpm build

# Production image
FROM node:18

# Install Python and dependencies
RUN apt-get update && apt-get install -y \
	python3 \
	python3-pip \
	ca-certificates \
	openssl \
	&& rm -rf /var/lib/apt/lists/*

# Update certificates
RUN update-ca-certificates

# Set shell for pnpm
ENV SHELL=/bin/sh

# Install pnpm globally and ensure it's in PATH
RUN npm install -g pnpm@latest
ENV PNPM_HOME="/root/.local/share/pnpm"
ENV PATH="${PNPM_HOME}:$PATH"

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"
ENV PYTHONPATH="/venv/lib/python3.12/site-packages"
ENV SSL_CERT_FILE="/etc/ssl/certs/ca-certificates.crt"
ENV REQUESTS_CA_BUNDLE="/etc/ssl/certs/ca-certificates.crt"
ENV PIP_CERT="/etc/ssl/certs/ca-certificates.crt"

# Copy built assets from builder
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/pnpm-lock.yaml ./pnpm-lock.yaml
COPY --from=builder /app/run_bot.py ./run_bot.py
COPY --from=builder /app/trading ./trading

# Install NLTK data
RUN python3 -c "import nltk; nltk.download('vader_lexicon'); nltk.download('punkt')"

# Set environment variables
ENV NODE_ENV=production
ENV PORT=8080
ENV HOST=0.0.0.0
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user
RUN groupadd -g 1001 nodejs && \
	useradd -u 1001 -g nodejs -s /bin/bash -m nextjs && \
	chown -R nextjs:nodejs /app && \
	chmod -R 755 /app && \
	mkdir -p /root/nltk_data && \
	chown -R nextjs:nodejs /root/nltk_data && \
	chmod -R 755 /root/nltk_data

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 8080

# Start the application
CMD ["pnpm", "next", "start", "-p", "8080", "-H", "0.0.0.0"]
