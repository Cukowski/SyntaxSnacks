# Admin Panel

The admin panel provides authorized administrators with tools to manage users, challenges, site content, and monitor activity.

## Access

To access the admin panel, you must be logged in as a user with the `is_admin` flag set to `True`.

On the first run, the application seeds the database with a default admin user:
- **Username**: `admin`
- **Password**: `admin123`

It is strongly recommended to change this password immediately after your first login.

## 1. User Management

The user management dashboard at `/admin/users` is the central hub for managing all registered users.

### Key Features
- **Search and Filter**: Find users by username or email. Filter the user list by status (`active`/`inactive`) or role (`admins`/`users`).
- **User Detail View**: Clicking on a user takes you to a detailed view (`/admin/users/<id>`) which shows:
    - Account information (username, email, XP, streak, etc.).
    - Total number of solved challenges.
    - A detailed **Audit Log** of all administrative actions performed on that user.
- **Account Actions**:
    - **Toggle Active/Inactive**: Deactivating a user prevents them from logging in.
    - **Toggle Admin Status**: Grant or revoke administrative privileges.
    - **Reset Password**: Generate a new, temporary password for a user.
    - **Adjust Stats**: Manually add or remove XP and streak points. A reason for the adjustment can be logged.

## 2. Challenge Management

Located at `/admin/challenges`, this section allows admins to curate the educational content of the site.

### Key Features
- **List and Filter**: View all challenges. Filter them by `status` (e.g., `published`, `draft`) or search by `tag`.
- **Add a New Challenge**: A form at `/admin/challenge/new` allows for the manual creation of a new challenge.
- **Publish/Unpublish**: Challenges can be toggled between `draft` and `published` states. Only published challenges are visible to users.
- **Export to CSV**: Download the filtered list of challenges as a CSV for editing or backup.
- **Bulk Import**:
    - Upload a `.csv` file at `/admin/challenges/import` to add multiple challenges at once.
    - The system provides a validation preview, showing which rows are valid and which contain errors.
    - Imports update existing challenges when titles match and skip duplicate rows.
    - **CSV Headers**: `title,prompt,hints,solution,language,difficulty,topic,tags,status,published_at`
    - A sample CSV can be downloaded from the import page.

## 3. Fun Cards Editor

The "Fun Cards" (jokes and fun facts) displayed on the Challenges page and home page are managed at `/admin/fun`. While the application can fall back to a CSV file, the primary way to manage this content is through the database via this interface.

### Key Features
- **Add and Delete**: Add new cards one by one or delete existing ones.
- **CSV Import/Export**:
    - Upload a CSV of new cards to add them in bulk.
    - Duplicate rows (same text/type) are skipped on import.
    - Export all existing cards to a CSV file for backup or external editing.

## 4. Contact Message Inbox

Submissions from the public "Contact Us" form are collected in the admin inbox, available at `/admin/messages`.

### Key Features
- **View and Filter**: See all incoming messages. Filter by status (`read`/`unread`) or perform a full-text search.
- **Manage Messages**:
    - Mark messages as read or unread.
    - Delete messages (soft delete).
- **Bulk Actions**: Select multiple messages to mark as read/unread or delete them all at once.
- **Export to CSV**: Export the current view of messages to a CSV file.
