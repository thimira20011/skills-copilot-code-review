# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign up for activities
- View active announcements in the site banner
- Manage announcements (authenticated users)

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   python app.py
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Sign up for an activity                                             |
| GET    | `/announcements`                                                  | Get active announcements for public display                         |
| GET    | `/announcements/manage?teacher_username=USERNAME`                 | Get all announcements for management                                |
| POST   | `/announcements/manage?teacher_username=USERNAME`                 | Create an announcement (JSON body)                                  |
| PUT    | `/announcements/manage/{announcement_id}?teacher_username=USERNAME` | Update an announcement (JSON body)                                |
| DELETE | `/announcements/manage/{announcement_id}?teacher_username=USERNAME` | Delete an announcement                                             |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

All data is stored in MongoDB.

### Announcements

Announcement payload fields:

- `message` (required, max 280 characters)
- `expiration_date` (required, `YYYY-MM-DD`)
- `start_date` (optional, `YYYY-MM-DD`)
