# FinTrade LMS - Setup Guide

This guide describes how to run both the FastAPI Backend and the React Frontend for local development.

## Prerequisites
- **Docker** and **Docker Compose** installed (for the backend and database)
- **Node.js** (v18+ recommended) and **npm** installed (for the frontend)

---

## 1. Starting the Backend

The backend is completely dockerized, including the PostgreSQL database, Redis, and FastAPI application.

1. Open your terminal and navigate to the backend docker directory:
   ```bash
   cd C:/FItTrade/lms-backend/docker
   ```

2. Generate or update your environment variables if needed. By default, the system should read from `.env` files in the backend root. Ensure you have a `.env` file patterned after `.env.example` inside `lms-backend`.

3. Start all services using Docker Compose:
   ```bash
   docker-compose up --build -d
   ```
   *(Appending `-d` runs the containers in detached mode. If you want to see logs live, simply remove `-d`)*.

4. **Verify the backend:**
   Once the containers are running, the API will be available at:
   - Base URL: `http://localhost:8000`
   - Interactive API Docs (Swagger UI): `http://localhost:8000/docs`

---

## 2. Starting the Frontend

The frontend is a Vite + React application.

1. Open a new terminal window and navigate to the frontend directory:
   ```bash
   cd C:/FItTrade/lms_frontend
   ```

2. **Verify Environment Variables:**
   Ensure you have a `.env` file in the `lms_frontend` root containing the API URL:
   ```env
   VITE_API_URL=http://localhost:8000
   ```

3. **Install Dependencies:**
   ```bash
   npm install
   ```

4. **Start the Development Server:**
   ```bash
   npm run dev
   ```

5. **Access the application:**
   The terminal will output a local URL (usually `http://localhost:5173`). Open this URL in your browser to access the application.

---

## 3. Stopping the Application

To shut everything down gracefully:

- **Frontend:** Press `Ctrl + C` in the terminal where the Vite server is running.
- **Backend:** Run the following command in the `lms-backend/docker` directory:
  ```bash
  docker-compose down
  ```
  *(This stops and removes the containers but preserves your database data in Docker volumes).*
