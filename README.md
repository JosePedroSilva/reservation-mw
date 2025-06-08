# Reservations Middleware Service

## Overview

This project implements a Reservations Middleware system consisting of two main services:
* **Reservation Middleware**: Handles the creation of reservations and publishes events to a Kafka topic.
* **Audit Middleware**: Consumes reservation events from Kafka and stores them as an audit trail in a PostgreSQL database.

The system uses Docker Compose to use the services, including PostgreSQL, Zookeeper, and Kafka.

---

## Prerequisites

Before you begin, ensure you have the following installed:
* Docker

---

## Setup and Running the Services

1.  **Clone the Repository** (if you haven't already):
    ```bash
    git clone <your-repository-url>
    cd <your-repository-directory>
    ```

2.  **Build and Start the Services**:
    Use Docker Compose to build the images and start all services in detached mode:
    ```bash
    docker compose build
    docker compose up -d
    ```
    This command will start:
    * `postgres` (Database)
    * `zookeeper` (Required for Kafka)
    * `kafka` (Message Broker)
    * `reservation-middleware` (Handles reservation creation)
    * `audit-middleware` (Audits reservation events)

3.  **Verify Services are Running**:
    You can check the status of the running containers:
    ```bash
    docker compose ps
    ```
    You should see all services listed with a state of `Up` or `healthy`.
    
---

## Accessing Services

* **Reservation Middleware API**:
    * Create Reservation (POST): 
    payload:
    ``` bash
    curl -X POST http://localhost:8000/reservations \
      -H "Content-Type: application/json" \
      -d '{
        "guest": {
          "first_name": "James",
          "last_name":  "Guest",
          "email":      "Guest@example.com",
          "phone":      "123-456-7890"
        },
        "source":         "Booking",
        "check_in_date":  "2025-07-01",
        "check_out_date": "2025-07-05"
      }'
  ``` 
    * List Reservations (GET): (for testing)
    ``` bash
      curl -i http://localhost:8000/reservations
    ``` 

* **Audit Middleware API**:
    * List Reservation Audits (GET): (for testing)
    ``` bash
      curl -i http://localhost:8001/reservations-audit
    ``` 
    
    * Health Check: `http://localhost:8001/healthz`
    ``` bash
      curl -i http://localhost:8001/healthz
    ``` 
## Visualizing Logs and Data

### Docker Compose Logs

You can view the logs for all services or individual services using Docker Compose:

* **View logs for all services (follow mode):**
    ```bash
    docker compose logs -f
    ```
* **View logs for a specific service (e.g., `reservation-middleware`):**
    ```bash
    docker compose logs -f reservation-middleware
    ```
    Replace `reservation-middleware` with `audit-middleware`, `kafka`, or `postgres` as needed.

### Kafka Messages (Reservations Topic)

``` bash
docker compose exec kafka \
  kafka-console-consumer.sh --bootstrap-server localhost:9092 \
  --topic reservations --from-beginning
```

The `scripts/read_topic.py` script can be used to consume and display messages from the `reservations` Kafka topic in real-time.
```bash
  python scripts/read_topic.py
```

To stop all running services:
```bash
docker-compose down
```