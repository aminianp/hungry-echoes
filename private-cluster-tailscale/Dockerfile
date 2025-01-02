# Use the official Go image as a build environment
FROM golang:1.22 AS build

# Set the working directory inside the container
WORKDIR /app

# Copy the go.mod file first to cache dependencies
COPY go.mod ./
RUN go mod download

# Copy the rest of the source code
COPY . .

# Build the Go app and name the output as "hungry-echoes"
RUN go build -o hungry-echoes main.go

# Use a minimal base image for the final container
FROM debian:stable-slim

# Set the working directory in the final container
WORKDIR /app

# Copy the compiled binary from the build stage to the final image
COPY --from=build /app/hungry-echoes .

# Expose port 8080 for the server
EXPOSE 8080

# Run the server binary
CMD ["./hungry-echoes"]
