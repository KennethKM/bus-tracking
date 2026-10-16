# Real-Time Bus Tracking and Journey Planning System

**A Django-based public transport application for Lusaka, Zambia, supporting live vehicle tracking, journey planning, and passenger–driver interactions.**

**[Live Application](https://bus-tracking6.onrender.com/)** · **[Source Code](https://github.com/KennethKM/bus-tracking)**

## Overview

This team-developed software engineering project connects passengers with live bus operations. Passengers can explore routes and stops, see active vehicles on a map, and manage boarding requests. Authorized drivers can manage assigned buses and send location updates from their mobile devices.

The application combines a Django REST Framework backend, a browser-based interface, public transport schedule data, and road-network routing services. It was developed as a final-year software engineering project at the University of Zambia.

## Key Features

### Passenger experience
- Register, sign in, and manage a passenger account.
- View active buses on an interactive map, including registration, status, speed, and last-update information.
- Search routes and select destinations and boarding stops.
- Create and manage waiting requests, including cancellation, boarding, and trip completion.
- Prevent multiple simultaneously active waiting requests for the same passenger.
- Journey planning and arrival-time prediction form part of the project's intended passenger-facing capabilities.

### Driver and fleet operations
- Authenticate drivers and identify their assigned buses.
- Restrict protected bus operations to active, appropriately assigned drivers.
- Activate or deactivate buses and start trips for selected routes and destinations.
- Receive location and speed updates from drivers' phones.
- Maintain vehicle state and the targeted stop during an active trip.
- View waiting-passenger counts for stops on an active trip.

## Backend Engineering Highlights

- **RESTful APIs:** Django REST Framework endpoints for authentication, route discovery, waiting requests, and bus operations.
- **Authorization:** Server-side checks restricting protected vehicle actions to eligible drivers with active bus assignments.
- **GPS ingestion:** Location and speed data from driver mobile devices feed the vehicle-tracking workflow.
- **Transport data:** General Transit Feed Specification (GTFS)-derived routes, trips, stops, and stop sequences support journey-related logic.
- **Road-network integration:** Open Source Routing Machine (OSRM) is used for road-distance calculations in backend trip and vehicle logic.
- **State management:** Backend services track bus operational status and progression through trip stops.
- **Persistence and deployment:** Django data models and migrations, with deployment dependencies for PostgreSQL, Gunicorn, and WhiteNoise.

## Technology Stack

| Area | Technologies |
| --- | --- |
| Backend | Python, Django, Django REST Framework |
| Databases | SQLite (development), PostgreSQL support via psycopg |
| Frontend | HTML, CSS, JavaScript |
| Maps | Leaflet, OpenStreetMap |
| Transport data | General Transit Feed Specification (GTFS) |
| Road routing | Open Source Routing Machine (OSRM) |
| Deployment | Render, Gunicorn, WhiteNoise |
| Collaboration | Git, GitHub |

## System Architecture

```text
Passenger browser                  Driver phone/browser
       |                                   |
       +----------------+------------------+
                        |
               Django web application
                        |
              Django REST Framework
                        |
       +----------------+----------------+
       |                |                |
 Authentication   Trip / vehicle    Passenger waiting
 & authorization  service logic     request handling
       |                |                |
       +----------------+----------------+
                        |
                 Django data layer
                        |
              Application database

External data/services:
- GTFS-derived transport data
- OSRM road-network distance service
- OpenStreetMap map tiles through Leaflet
```

This diagram is a conceptual overview of the principal components, not a complete deployment or network diagram.

## Selected API Endpoints

The backend exposes routes under `/api/`. Examples documented in the project include:

| Capability | Method | Endpoint |
| --- | --- | --- |
| Passenger registration | POST | `/api/auth/register/` |
| Passenger login | POST | `/api/auth/login/` |
| Current passenger | GET | `/api/auth/me/` |
| Passenger logout | POST | `/api/auth/logout/` |
| Route search | GET | `/api/routes/search/?q=<search-term>` |
| Route destinations | GET | `/api/routes/<route_id>/destinations/` |
| Stops for destination | GET | `/api/routes/<route_id>/stops/?destination=<destination>` |
| Waiting requests | GET / POST | `/api/waiting-requests/` |
| Mark boarded | POST | `/api/waiting-requests/<id>/board/` |
| Cancel request | POST | `/api/waiting-requests/<id>/cancel/` |
| Complete trip | POST | `/api/waiting-requests/<id>/complete/` |
| Driver login | POST | `/api/auth/driver/login/` |
| Assigned buses | GET | `/api/auth/driver/buses/` |
| Start trip | POST | `/api/buses/start-trip/` |
| Submit bus location | POST | `/api/buses/<registration_number>/location/` |
| Waiting overview | GET | `/api/buses/<registration_number>/waiting-overview/` |

Protected endpoints require the appropriate authentication and authorization. This table is a selection, not an exhaustive API reference.

## Local Development

### Prerequisites

- Python compatible with the project's pinned dependencies
- Git
- A suitable database and configuration for the selected environment
- Access to any external services required by the functionality you want to test

### Installation

```bash
git clone https://github.com/KennethKM/bus-tracking.git
cd bus-tracking
python -m venv venv
```

Activate the environment:

**Windows (Command Prompt):**
```bat
venv\Scripts\activate
```

**macOS / Linux:**
```bash
source venv/bin/activate
```

Install the pinned dependencies:

```bash
pip install -r requirements.txt
```

After configuring the required environment variables and database for your local environment:

```bash
python manage.py migrate
python manage.py runserver
```

The development server normally starts at `http://127.0.0.1:8000/`.

**Configuration note:** This repository has deployment-specific settings and external-service dependencies. Do not use production secrets in a local environment or commit credentials to version control. Some functions, including road-network calculations, require the relevant external service to be configured and available.

## Using the Application

**Passengers:** Open the application, register or sign in, search for a route, select a destination and boarding stop, and manage the resulting waiting request as the journey progresses.

**Drivers:** Sign in using an authorized driver account, select an assigned bus, activate it, start a trip, and allow location updates from the driver's device. Driver permissions and active assignments are checked by the backend.

The live homepage is available at **https://bus-tracking6.onrender.com/**. Some functionality requires an appropriate user account and, for live vehicle data, an active driver-operated trip.

## Testing and Engineering Practices

The project includes backend testing, debugging, and collaborative Git/GitHub development. Relevant areas of testing include authentication, authorization, bus operations, route-related behavior, and passenger request handling.

For a precise list of automated tests and current results, inspect the test modules and run the suite in a correctly configured environment. No unverified pass count is asserted here.

## Project Team and Contributions

This was a **collaborative final-year software engineering project**.

**Kenneth Kaunda Musonda — Backend Developer / Team Lead**

My work included backend service and REST API development, driver authentication and authorization, integration of live GPS updates, GTFS-related data handling, OSRM integration, and backend trip/vehicle logic. I also participated in debugging, testing, and Git/GitHub collaboration.

Other project components were developed collaboratively with team members; the repository's Git history provides additional detail about contributions.

## Project Links

- **Live demo:** https://bus-tracking6.onrender.com/
- **GitHub repository:** https://github.com/KennethKM/bus-tracking
- **Primary branch:** `integration` (default branch and deployed code line)

---

*University of Zambia — Bachelor of Computer Science (Software Engineering) final-year project.*
