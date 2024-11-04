# Use the official Go image as a build environment
FROM golang:1.22 AS build

# Set the working directory inside the container
WORKDIR /app

# Copy the source code into the container
COPY . .

# Build the Go app
RUN go build -o hungry-echoes .

# Use a minimal base image
FROM alpine:latest

# Set the working directory inside the container
WORKDIR /app

# Copy the compiled binary from the build environment
COPY --from=build /app/hungry-echoes .

# Expose port 8080
EXPOSE 8080

# Run the echo server
CMD ["./hungry-echoes"]