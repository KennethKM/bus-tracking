# Bus Tracking System

A web-based public bus tracking system built with Django and Django REST Framework.

The system supports real-time bus location updates, journey planning using GTFS-derived transport data, passenger waiting requests, and driver authorization for bus operations.

## Features

### Passenger Features

- View active buses on an interactive map.
- View a bus registration number, current status, speed and most recent update time.
- Register, log in and log out of a passenger account.
- Search available routes.
- Select a route, destination and boarding stop.
- Create and view personal waiting requests.
- Cancel a waiting request before boarding.
- Mark a waiting request as boarded.
- Complete an on-board trip and create another waiting request afterwards.
- Prevent a passenger from creating more than one active request at a time.

### Bus and Driver Features

- Activate and deactivate buses.
- Start a bus trip using a selected route and destination.
- Receive GPS updates containing latitude, longitude and speed.
- Store the current bus location, speed, operational status and latest update time.
- Maintain the current targeted stop during an active trip.
- Provide waiting-passenger counts for stops on an active trip.
- Authenticate drivers through Django user accounts.
- Restrict bus operations to active drivers assigned to the relevant bus.

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

1. Clone the repository:

   ```bash
   git clone https://github.com/KennethKM/bus-tracking.git
   cd bus-tracking
   ```

2. Switch to the integration branch:

   ```bash
   git switch --track origin/integration
   ```

3. Create a virtual environment:

   ```bash
   python -m venv venv
   ```

4. Activate the virtual environment.

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

## Using the System

### Passenger

1. Open the passenger interface.
2. Register an account or log in.
3. Select a route, destination and boarding stop.
4. Create a waiting request.
5. Use **Mark as Boarded** after boarding the bus.
6. Use **Complete Trip** after reaching the destination.
7. Create another waiting request when the previous trip is completed.

### Driver

1. Log in using a driver account.
2. Select a bus assigned to that driver.
3. Activate the bus.
4. Start a trip by selecting a route and destination.
5. Send GPS updates for the selected bus.
6. View waiting-passenger counts for stops on the active trip.
7. Deactivate the bus when its operation ends.

## API Endpoints

All API routes begin with `/api/`.

| Function | Endpoint |
|---|---|
| Passenger registration | `POST /api/auth/register/` |
| Passenger login | `POST /api/auth/login/` |
| Current passenger | `GET /api/auth/me/` |
| Passenger logout | `POST /api/auth/logout/` |
| Route search | `GET /api/routes/search/?q=<search-term>` |
| Route destinations | `GET /api/routes/<route_id>/destinations/` |
| Trip stops | `GET /api/routes/<route_id>/stops/?destination=<destination>` |
| Waiting requests | `GET` or `POST /api/waiting-requests/` |
| Mark request as boarded | `POST /api/waiting-requests/<id>/board/` |
| Cancel waiting request | `POST /api/waiting-requests/<id>/cancel/` |
| Complete trip | `POST /api/waiting-requests/<id>/complete/` |
| Driver login | `POST /api/auth/driver/login/` |
| Assigned buses | `GET /api/auth/driver/buses/` |
| Start trip | `POST /api/buses/start-trip/` |
| Update bus location | `POST /api/buses/<registration_number>/location/` |
| Waiting overview | `GET /api/buses/<registration_number>/waiting-overview/` |