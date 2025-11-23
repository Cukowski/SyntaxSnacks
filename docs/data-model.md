# Data Model

The application uses several SQLAlchemy models to structure its data in the database.

### User

*   `id`: (Integer) Primary Key
*   `username`: (String) Unique username for login.
*   `email`: (String) Unique user email.
*   `password_hash`: (String) Hashed password.
*   `xp`: (Integer) Experience points earned by the user.
*   `streak`: (Integer) Current daily challenge completion streak.
*   `last_active_date`: (Date) The last date a challenge was solved, used for streak calculation.
*   `is_admin`: (Boolean) Flag to indicate if the user has admin privileges.

### Challenge

*   `id`: (Integer) Primary Key
*   `title`, `prompt`, `solution`, `hints`: (String) Core content of the challenge.
*   `language`, `difficulty`, `topic`: (String) Metadata for categorizing the challenge.
*   `added_by`: (Integer) Foreign Key to `User.id`.

### Submission

*   `id`, `user_id`, `challenge_id`, `timestamp`: Records a user's successful completion of a challenge.

### Message

*   `id`, `name`, `email`, `body`, `created_at`: Stores a submission from the contact form.
*   `is_read`: (Boolean) For the admin inbox to track message status.
*   `deleted_at`: (DateTime) For soft-deleting messages.