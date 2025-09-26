# Build stage
FROM golang:1.22 AS build
WORKDIR /src

COPY go.mod go.sum ./
RUN go mod download

COPY services/ledger/ /src/services/ledger/
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o /out/ledger ./services/ledger

# Runtime (distroless, non-root)
FROM gcr.io/distroless/base-debian11
WORKDIR /app
COPY --from=build /out/ledger /app/ledger
USER nonroot
EXPOSE 8088
ENTRYPOINT ["/app/ledger"]