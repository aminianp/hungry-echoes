package main

import (
	"database/sql"
	"fmt"
	"net/http"
	"os"

	_ "github.com/lib/pq" // Make sure to include the PostgreSQL driver
)

// Global database variable
var db *sql.DB

// Initialize the database connection
func initDB() error {
	dbHost := os.Getenv("DB_HOST")
	dbPort := os.Getenv("DB_PORT")
	dbUser := os.Getenv("DB_USER")
	dbPassword := os.Getenv("DB_PASSWORD")
	dbName := os.Getenv("DB_NAME")

	connStr := fmt.Sprintf("host=%s port=%s user=%s password=%s dbname=%s sslmode=disable",
		dbHost, dbPort, dbUser, dbPassword, dbName)

	var err error
	db, err = sql.Open("postgres", connStr)
	return err
}

// Handle incoming HTTP requests
func handleRequest(w http.ResponseWriter, r *http.Request) {
	message := r.URL.Query().Get("message")
	if message == "" {
		http.Error(w, "Query parameter 'message' is required", http.StatusBadRequest)
		return
	}

	var corporatePhrase string
	// Select a random phrase from the database
	err := db.QueryRow("SELECT sentence FROM corporate.jargons ORDER BY RANDOM() LIMIT 1").Scan(&corporatePhrase)
	if err != nil {
		http.Error(w, "Failed to retrieve phrase", http.StatusInternalServerError)
		return
	}

	// Format the response with the retrieved phrase, remote address, and message
	response := fmt.Sprintf(corporatePhrase, r.RemoteAddr, message)
	fmt.Fprintln(w, response)
}

func main() {
	// Define the port to listen on
	port := ":8080"

	// Initialize the database connection
	err := initDB()
	if err != nil {
		fmt.Println("Error initializing database:", err)
		return
	}
	defer db.Close()

	// Set up the handler for HTTP requests
	http.HandleFunc("/", handleRequest)

	// Start the HTTP server
	fmt.Println("HTTP echo server started on port", port)
	if err := http.ListenAndServe(port, nil); err != nil {
		fmt.Println("Error starting server:", err)
	}
}