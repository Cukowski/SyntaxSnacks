# Data Model

The application uses several SQLAlchemy models to structure its data in the database.

### User

| Column           | Type      | Description                                                 |
| ---------------- | --------- | ----------------------------------------------------------- |
| `id`             | Integer   | Primary Key                                                 |
| `username`       | String    | Unique username for login.                                  |
| `email`          | String    | Unique user email.                                          |
| `password_hash`  | String    | Hashed password.                                            |
| `active`         | Boolean   | If `False`, the user cannot log in. Defaults to `True`.     |
| `xp`             | Integer   | Experience points earned by the user.                       |
| `streak`         | Integer   | Current daily challenge completion streak.                  |
| `last_login`     | DateTime  | Records the timestamp of the user's last successful login.  |
| `last_active_date` | Date    | The last date a challenge was solved, used for streak calculation. |
| `is_admin`       | Boolean   | Flag to indicate if the user has admin privileges.          |
| `created_at`     | DateTime  | Timestamp of when the user account was created.             |

### Challenge

| Column         | Type     | Description                                                          |
| -------------- | -------- | -------------------------------------------------------------------- |
| `id`           | Integer  | Primary Key                                                          |
| `title`        | String   | The title of the challenge.                                          |
| `prompt`       | Text     | The main body/question of the challenge.                             |
| `solution`     | Text     | The correct answer or code for the challenge.                        |
| `hints`        | Text     | Optional hints to help the user.                                     |
| `language`     | String   | The programming language or category (e.g., "Python", "JavaScript"). |
| `difficulty`   | String   | The difficulty level (e.g., "Easy", "Medium", "Hard").               |
| `topic`        | String   | The subject area, used to group challenges into Dungeons.            |
| `tags`         | Text     | A comma-separated string of tags for filtering.                      |
| `status`       | String   | The status of the challenge (`draft` or `published`).                |
| `published_at` | DateTime | The timestamp when the challenge was published.                      |
| `added_by`     | Integer  | Foreign Key to `User.id` of the admin who added it.                  |

### Submission

Records a user's successful completion of a challenge.

| Column         | Type     | Description                                 |
| -------------- | -------- | ------------------------------------------- |
| `id`           | Integer  | Primary Key                                 |
| `user_id`      | Integer  | Foreign Key to `User.id`.                   |
| `challenge_id` | Integer  | Foreign Key to `Challenge.id`.              |
| `timestamp`    | DateTime | The time the submission was made.           |

### Joke

Stores the "fun facts" and "jokes" displayed on the home page and Challenges page.

| Column       | Type    | Description                                    |
| ------------ | ------- | ---------------------------------------------- |
| `id`         | Integer | Primary Key                                    |
| `text`       | Text    | The content of the joke or fact.               |
| `entry_type` | String  | The type of entry, either `fun` or `fact`.     |

### Dungeon

A collection of challenges grouped by a common `topic`.

| Column        | Type    | Description                                                        |
| ------------- | ------- | ------------------------------------------------------------------ |
| `id`          | Integer | Primary Key                                                        |
| `name`        | String  | The name of the dungeon.                                           |
| `description` | Text    | A brief description of the dungeon's theme.                        |
| `topic`       | String  | The topic that links this dungeon to a group of `Challenge` records. |
| `unlock_xp`   | Integer | The amount of XP a user needs to see this dungeon.                 |
| `reward_xp`   | Integer | The bonus XP awarded for completing all challenges in the dungeon.   |

### DungeonCompletion

Marks that a user has completed all challenges within a dungeon.

| Column         | Type     | Description                     |
| -------------- | -------- | ------------------------------- |
| `id`           | Integer  | Primary Key                     |
| `user_id`      | Integer  | Foreign Key to `User.id`.       |
| `dungeon_id`   | Integer  | Foreign Key to `Dungeon.id`.    |
| `completed_at` | DateTime | When the dungeon was completed. |

### PuzzleCompletion

Records a user's completion of a specific mini-game puzzle to prevent repeat XP awards.

| Column        | Type     | Description                     |
| ------------- | -------- | ------------------------------- |
| `id`          | Integer  | Primary Key                     |
| `user_id`     | Integer  | Foreign Key to `User.id`.       |
| `puzzle_name` | String   | A unique identifier for the puzzle (e.g., `bit_flipper_lvl_1`). |
| `completed_at`| DateTime | When the puzzle was completed.  |

### AuditLog

Tracks administrative actions performed on users.

| Column          | Type    | Description                                                        |
| --------------- | ------- | ------------------------------------------------------------------ |
| `id`            | Integer | Primary Key                                                        |
| `actor_user_id` | Integer | Foreign Key to the `User.id` of the admin who performed the action.  |
| `target_user_id`| Integer | Foreign Key to the `User.id` of the user who was the subject of the action. |
| `action`        | String  | A description of the action taken (e.g., `toggle_active`, `reset_password`). |
| `meta`          | JSON    | A JSON blob containing extra data about the action (e.g., `{ "active": true }`). |
| `created_at`    | DateTime| When the action occurred.                                          |

### Message

Stores a submission from the contact form.

| Column       | Type     | Description                             |
| ------------ | -------- | --------------------------------------- |
| `id`         | Integer  | Primary Key                             |
| `name`       | String   | Name of the person who submitted.       |
| `email`      | String   | Email of the person who submitted.      |
| `body`       | Text     | The content of the message.             |
| `created_at` | DateTime | When the message was submitted.         |
| `is_read`    | Boolean  | For the admin inbox to track status.    |
| `deleted_at` | DateTime | For soft-deleting messages.             |
