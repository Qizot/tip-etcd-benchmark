FROM golang:alpine AS builder

WORKDIR /app
RUN apk update && apk add --no-cache git

COPY go.mod ./
COPY go.sum ./
RUN go mod download


COPY main.go main.go
RUN CGO_ENABLED=0 go build -o /benchmark 

FROM scratch
COPY --from=builder /benchmark /bin/benchmark
# The CMD should be replaced with a proper benchmark command line arguments and run via `docker run ...`
CMD [ "/bin/benchmark"]