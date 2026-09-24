

````markdown
# Bus Tracking System

A Django and Django REST Framework web application for tracking public buses using real GPS location updates from a driver's GPS-enabled device.

The system uses GTFS-derived transport data to represent routes, trips, stops, stop sequences and shapes. It provides a browser-based passenger interface for viewing active buses, planning a journey and managing waiting requests.

> **Note:** GPS simulation and the `/move/` endpoint were early prototypes and are not part of the current system.

## Implemented Features

### Passenger Functions

- View active buses on an interactive Leaflet and OpenStreetMap map.
- Register, log in and log out of a passenger account.
- Search available routes.
- Select a destination and boarding stop for a trip.
- Create and view personal waiting requests.
- Cancel a request while its status is `WAITING`.
- Mark a `WAITING` request as `ON_BOARD`.
- Complete an `ON_BOARD` trip, changing its status to `COMPLETED` so that the passenger can request another ride.
- Prevent more than one active `WAITING` or `ON_BOARD` request for the same passenger.

### Bus and Driver Backend Functions

- Store the latest bus latitude, longitude, speed, status and update time directly on the `Bus` record.
- Support bus operational statuses: `IDLE`, `IN_TRANSIT` and `AT_STOP`.
- Start a trip by selecting a route and destination.
- Process GPS location updates using a bus registration number.
- Maintain the current targeted stop for an active trip.
- Provide waiting-request counts for stops on an active trip.
- Authenticate drivers through Django user accounts.
- Restrict protected bus operations to active drivers with an active assignment to the relevant bus.

Protected driver operations include bus activation, deactivation, operational reset, trip start and GPS location updates.

## Technology Stack

- Python
- Django
- Django REST Framework
- SQLite
- HTML, CSS and JavaScript
- Leaflet
- OpenStreetMap
- GTFS-derived transport data

## Setup

The current shared project work is on the `integration` branch.

1. Clone the repository:

   ```bash
   git clone https://github.com/KennethKM/bus-tracking.git
   cd bus-tracking
````

2. Switch to the integration branch:

   ```bash
   git switch --track origin/integration
   ```

3. Create a virtual environment:

   ```bash
   python -m venv venv
   ```

4. Activate it.

   On Windows:

   ```bash
   venv\Scripts\activate
   ```

   On macOS or Linux:

   ```bash
   source venv/bin/activate
   ```

5. Install dependencies:

   ```bash
   pip install django djangorestframework
   ```

6. Apply database migrations:

   ```bash
   python manage.py migrate
   ```

7. Start the development server:

   ```bash
   python manage.py runserver
   ```

8. Open the passenger interface:

   ```text
   http://127.0.0.1:8000/
   ```

The Django administration interface is available at:

```text
http://127.0.0.1:8000/admin/
```

## Transport Data

The application requires GTFS-derived transport records for routes, trips, stops, stop times and shapes. The SQLite database is not included in the repository, so a fresh setup must load the project’s transport data before route selection and trip-related functions can be used.

## API Overview

All API routes begin with `/api/`.

| Purpose                          | Endpoint                                                      |
| -------------------------------- | ------------------------------------------------------------- |
| Passenger registration           | `POST /api/auth/register/`                                    |
| Passenger login                  | `POST /api/auth/login/`                                       |
| Current passenger                | `GET /api/auth/me/`                                           |
| Passenger logout                 | `POST /api/auth/logout/`                                      |
| Search routes                    | `GET /api/routes/search/?q=<search-term>`                     |
| Route destinations               | `GET /api/routes/<route_id>/destinations/`                    |
| Stops for a selected destination | `GET /api/routes/<route_id>/stops/?destination=<destination>` |
| Passenger waiting requests       | `GET` or `POST /api/waiting-requests/`                        |
| Mark request as boarded          | `POST /api/waiting-requests/<id>/board/`                      |
| Cancel waiting request           | `POST /api/waiting-requests/<id>/cancel/`                     |
| Complete passenger trip          | `POST /api/waiting-requests/<id>/complete/`                   |
| Driver login                     | `POST /api/auth/driver/login/`                                |
| Assigned driver buses            | `GET /api/auth/driver/buses/`                                 |
| Start bus trip                   | `POST /api/buses/start-trip/`                                 |
| Update bus GPS location          | `POST /api/buses/<registration_number>/location/`             |

## Current Scope

The passenger interface is integrated with the current backend. The driver backend endpoints and driver-to-bus authorization are implemented. The separately developed driver interface still requires final adaptation and integration with the current backend.

ETA functionality is not yet integrated and verified as a complete passenger-facing feature.

```
```
