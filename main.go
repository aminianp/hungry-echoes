package main

import (
	"fmt"
	"net/http"
)

func main() {
	// Define the port to listen on
	port := ":8080"
	
	// Set up the handler for HTTP requests
	http.HandleFunc("/", handleRequest)
	
	// Start the HTTP server
	fmt.Println("HTTP echo server started on port", port)
	if err := http.ListenAndServe(port, nil); err != nil {
		fmt.Println("Error starting server:", err)
	}
}

func handleRequest(w http.ResponseWriter, r *http.Request) {
	// Log the client address and request details
	fmt.Println("Client connected:", r.RemoteAddr)

	// Read input message from the query parameter "message"
	message := r.URL.Query().Get("message")
	if message == "" {
		message = "Hello, please provide a message in the 'message' query parameter."
	}

	// Construct the echo response message
	echoMessage := fmt.Sprintf("Echoing what %s said, I also believe %s! That said, we need to stay hungry!", r.RemoteAddr, message)
	fmt.Println("Sending:", echoMessage)

	// Write the response message back to the client
	fmt.Fprintln(w, echoMessage)
}