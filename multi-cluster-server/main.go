package main

import (
	"database/sql"
	"fmt"
	"net/http"
	"os"

	_ "github.com/lib/pq" // PostgreSQL driver
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

// Global database variable
var db *sql.DB

// Prometheus metrics
var (
	requestCount = prometheus.NewCounter(
		prometheus.CounterOpts{
			Name: "hungry_echoes_request_count",
			Help: "Total number of requests processed",
		},
	)
	errorCount = prometheus.NewCounter(
		prometheus.CounterOpts{
			Name: "hungry_echoes_error_count",
			Help: "Total number of errors encountered",
		},
	)
	dbErrorCount = prometheus.NewCounter(
		prometheus.CounterOpts{
			Name: "hungry_echoes_db_error_count",
			Help: "Total number of database errors",
		},
	)
)

func init() {
	// Register Prometheus metrics
	prometheus.MustRegister(requestCount)
	prometheus.MustRegister(errorCount)
	prometheus.MustRegister(dbErrorCount)
}

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
	if err != nil {
		errorCount.Inc() // Increment error count for Prometheus
		fmt.Println("Error initializing database:", err)
	}
	return err
}

// Handle incoming HTTP requests
func handleRequest(w http.ResponseWriter, r *http.Request) {
	requestCount.Inc() // Increment request count

	message := r.URL.Query().Get("message")
	if message == "" {
		errorCount.Inc() // Increment error count for missing parameter
		http.Error(w, "Query parameter 'message' is required", http.StatusBadRequest)
		return
	}

	var corporatePhrase string
	// Select a random phrase from the database
	err := db.QueryRow("SELECT sentence FROM corporate.jargons ORDER BY RANDOM() LIMIT 1").Scan(&corporatePhrase)
	if err != nil {
		dbErrorCount.Inc() // Increment DB error count for Prometheus
		errorCount.Inc()    // Increment error count for Prometheus
		http.Error(w, "Failed to retrieve phrase", http.StatusInternalServerError)
		fmt.Println("Database query error:", err) // Log the error
		return
	}

	// Format the response with the retrieved phrase, remote address, and message
	response := fmt.Sprintf(corporatePhrase, r.RemoteAddr, message)
	fmt.Fprintln(w, response)
}

func main() {
	// Define the main server port and metrics port
	appPort := ":8080"
	metricsPort := ":8081"

	// Initialize the database connection
	err := initDB()
	if err != nil {
		fmt.Println("Error initializing database:", err)
		return
	}
	defer db.Close()

	// Set up the handler for HTTP requests on the main server
	http.HandleFunc("/", handleRequest)

	// Run the main application server in a goroutine
	go func() {
		fmt.Println("HTTP echo server started on port", appPort)
		if err := http.ListenAndServe(appPort, nil); err != nil {
			errorCount.Inc() // Increment error count if server fails to start
			fmt.Println("Error starting server:", err)
		}
	}()

	// Set up the metrics server with the /metrics endpoint
	metricsMux := http.NewServeMux()
	metricsMux.Handle("/metrics", promhttp.Handler())

	// Start the metrics server on a separate port
	fmt.Println("Metrics server started on port", metricsPort)
	if err := http.ListenAndServe(metricsPort, metricsMux); err != nil {
		errorCount.Inc() // Increment error count if metrics server fails to start
		fmt.Println("Error starting metrics server:", err)
	}
}