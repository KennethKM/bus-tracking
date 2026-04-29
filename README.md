# Bus Tracking System

A Django REST API that simulates real-time bus movement along predefined routes.

## Features

* Create routes and stops
* Assign buses to routes
* Move buses manually via API
* Automatic simulation using a management command

## Setup

1. Clone repo:
   git clone https://github.com/KennethKM/bus-tracking.git

2. Create virtual environment:
   python -m venv venv

3. Activate:
   venv\Scripts\activate

4. Install dependencies:
   pip install django djangorestframework

5. Run migrations:
   python manage.py migrate

6. Run server:
   python manage.py runserver

7. Run simulation:
   python manage.py simulate_buses

## API Example

Move a bus:
POST /api/buses/1/move/
