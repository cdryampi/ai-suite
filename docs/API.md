# API Documentation

The AI Suite Backend exposes a RESTful API for managing mini apps, jobs, and artifacts.

**Base URL**: `http://localhost:5000`

## Core Endpoints

### Health Check
GET `/api/health`

Returns the system status.

**Response:**
```json
{
  "status": "ok",
  "version": "0.1.0",
  "environment": "development"
}
```

## Mini App Endpoints

### Run Mini App
POST `/api/miniapps/{app_id}/run`

Starts a new execution workflow.

**Body:**
```json
{
  "input": "https://example.com/property",
  "variant": 1,
  "options": {}
}
```

**Response:**
```json
{
  "status": "ok",
  "job_id": "job_123abc...",
  "logs": ["Starting workflow..."],
  "artifacts": [],
  "result": {}
}
```

### Get Job Status
GET `/api/miniapps/{app_id}/status/{job_id}`

Poll this endpoint to get real-time progress.

**Response:**
```json
{
  "job_id": "job_123abc...",
  "status": "running", // pending, running, complete, failed
  "created_at": "2024-01-01T10:00:00",
  "logs": [
    "Starting workflow...",
    "Scraping URL...",
    "Analyzing content..."
  ],
  "error": null
}
```

### Get Artifact
GET `/api/miniapps/{app_id}/artifact/{job_id}/{filename}`

Download a generated file.

**Response**: File stream (application/json, text/plain, etc.)

### Get Mini App Info
GET `/api/miniapps/{app_id}/info`

Get metadata about a mini app.

**Response:**
```json
{
  "id": "realestate_ads",
  "name": "Real Estate Ad Generator",
  "description": "...",
  "version": "1.0.0",
  "variants": {
    "1": "Basic",
    "2": "Detailed"
  }
}
```
