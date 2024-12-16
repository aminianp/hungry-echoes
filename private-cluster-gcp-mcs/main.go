package main

import (
	"database/sql"
	"fmt"
	"net/http"
	"os"

	_ "github.com/lib/pq"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

// Port configurations
const (
	AppPort     = ":8080"
	MetricsPort = ":8081"
)

// Global variables
var (
	db *sql.DB

	// Prometheus metrics
	requestCounter = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "hungry_echoes_requests_total",
			Help: "Total number of requests to the echo server",
		},
		[]string{"status"}, // Label for success/error
	)

	dbErrorCounter = promauto.NewCounter(
		prometheus.CounterOpts{
			Name: "hungry_echoes_db_errors_total",
			Help: "Total number of database errors",
		},
	)
)

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
		requestCounter.WithLabelValues("error").Inc()
		http.Error(w, "Query parameter 'message' is required", http.StatusBadRequest)
		return
	}

	var corporatePhrase string
	// Select a random phrase from the database
	err := db.QueryRow("SELECT sentence FROM corporate.jargons ORDER BY RANDOM() LIMIT 1").Scan(&corporatePhrase)
	if err != nil {
		requestCounter.WithLabelValues("error").Inc()
		dbErrorCounter.Inc() // Increment DB error counter
		http.Error(w, "Failed to retrieve phrase", http.StatusInternalServerError)
		return
	}

	// Format the response with the retrieved phrase, remote address, and message
	response := fmt.Sprintf(corporatePhrase, r.RemoteAddr, message)
	fmt.Fprintln(w, response)
	requestCounter.WithLabelValues("success").Inc()
}

func main() {
	// Initialize the database connection
	err := initDB()
	if err != nil {
		fmt.Println("Error initializing database:", err)
		return
	}
	defer db.Close()

	// Create a new mux for the main application
	mainMux := http.NewServeMux()
	mainMux.HandleFunc("/", handleRequest)

	// Create a new mux for metrics
	metricsMux := http.NewServeMux()
	metricsMux.Handle("/metrics", promhttp.Handler())

	// Start the metrics server on a different port
	go func() {
		fmt.Printf("Metrics server started on %s\n", MetricsPort)
		if err := http.ListenAndServe(MetricsPort, metricsMux); err != nil {
			fmt.Printf("Error starting metrics server on %s: %v\n", MetricsPort, err)
		}
	}()

	// Start the main application server
	fmt.Printf("HTTP echo server started on %s\n", AppPort)
	if err := http.ListenAndServe(AppPort, mainMux); err != nil {
		fmt.Printf("Error starting main server on %s: %v\n", AppPort, err)
	}
}