package main

import (
	"bufio"
	"fmt"
	"net"
)

func main () {
	// Define the port to listen on

	port := ":8080"

	// Start listening on the specified port
	listener, err := net.Listen("tcp", port)
	if err != nil {
		fmt.Println("Error starting server:", err)
		return
	}

	defer listener.Close()
	fmt.Println("Echo server started on port", port)

	for {
		// Accept a new connection
		conn, err := listener.Accept()
		if err != nil {
			fmt.Println("Error accepting conncetion:", err)
		}

		// Handle each connection in a new goroutine
		go handleConnection(conn)
	}
}

func handleConnection(conn net.Conn) {
	defer conn.Close()

	fmt.Println("Client connected:", conn.RemoteAddr())

	// Read data from connection and echo it back
	scanner := bufio.NewScanner(conn)
	for scanner.Scan() {
		// Get the input from the client
		text := scanner.Text()
		echoMessage := fmt.Sprintf("Echoing what %s said, I also believe %s! That said, we need to stay hungry!", conn.RemoteAddr(), text)
		fmt.Println("Sending: ", echoMessage)
		_, err := conn.Write([]byte(echoMessage + "\n"))

		if err != nil {
			fmt.Println("Error writing to connection:", err)
			return
		}
	}

	if err := scanner.Err(); err != nil {
		fmt.Println("Error reading from connection:", err)
	}
	fmt.Println("Client disconnected:", conn.RemoteAddr())
}
