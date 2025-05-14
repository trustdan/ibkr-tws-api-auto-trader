FROM golang:1.21-alpine as builder

WORKDIR /app

# Copy go.mod and go.sum files first (for better caching)
COPY go.mod go.sum ./
RUN go mod download

# Copy the source code
COPY . .

# Build the application with optimizations
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -ldflags="-s -w" -o scanner cmd/scanner/main.go

# Use a small alpine image for the final stage
FROM alpine:3.18

WORKDIR /app

# Copy the binary from the builder stage
COPY --from=builder /app/scanner .

# Install CA certificates for HTTPS
RUN apk --no-cache add ca-certificates

# Create non-root user
RUN adduser -D -H -h /app scanner
USER scanner

# Set default environment variables
ENV PORT=8080
ENV LOG_LEVEL=info

# Expose the port
EXPOSE 8080

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD wget -q -O- http://localhost:8080/health || exit 1

# Run the binary
CMD ["./scanner"] 