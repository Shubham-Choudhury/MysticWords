# MysticWords

MysticWords is a web application designed to facilitate the creation, management, and publication of articles or blog posts. It provides a user-friendly interface for authors to write and publish their content, as well as for readers to explore articles across various categories.

## Features:

1. **User Authentication:** Users can sign up for an account, sign in, and log out securely. Passwords are hashed for security.

2. **Author Profiles:** Authors have their own profiles where they can provide information about themselves, including a bio, social media links, and profile picture.

3. **Article Management:** Authors can create, edit, delete, and publish articles. They can also upload multiple images for each article.

4. **Category Management:** Articles can be categorized into different topics for easy navigation and discovery.

5. **Search and Filter:** Readers can search for articles using keywords and filter articles by category.

6. **Pagination:** Articles are paginated to improve readability and load times.

7. **Error Handling:** Custom error pages are provided for 404 errors.

## Implementation:

- The backend is built using Flask, a lightweight web framework in Python.

- User authentication is handled using Flask-Login, with passwords hashed using Werkzeug's security features.

- Data is stored in an SQLite database using Flask-SQLAlchemy.

- Articles can have multiple images associated with them, stored in the filesystem and referenced in the database.

- Categories are predefined and stored in the database. Articles are associated with categories using foreign keys.

- Form validation is implemented to ensure that all required fields are filled out correctly.

- Image upload is restricted to certain file formats and sizes for security and performance reasons.

## Usage:

- **Sign Up:** New users can create an account by providing their name, email, username, and password.
- **Sign In:** Registered users can sign in using their email and password.
- **Profile Editing:** Authors can edit their profiles to update their information and profile picture.
- **Article Management:** Authors can create, edit, delete, and publish articles, including uploading images.
- **Category Exploration:** Readers can explore articles by category and navigate through paginated lists of articles.
- **Search and Filter:** Readers can search for articles using keywords and filter them by category.
- **Logout:** Users can log out securely when they're done.

## **ADD THIS TO RESUME**

**Title:** MysticWords - Web Application

**Details:**

- Developed the MysticWords web application using Python and Flask, aimed at providing a platform for content creation and sharing within a community setting. The application serves as a medium for users to publish articles, explore various categories, and interact with authors.

- Implemented robust user authentication features leveraging Flask-Login, ensuring secure access to the application's functionalities. This included features such as user registration, login, password hashing, and session management, enhancing the overall security of the platform.

- Designed a scalable and efficient relational database schema using SQLAlchemy to model key entities such as user profiles, articles, categories, and article images. This allowed for seamless data storage and retrieval operations, optimizing performance and scalability.

- Utilized Flask's powerful routing system to create intuitive endpoints for essential features such as creating, editing, and publishing articles, browsing articles by category, managing user profiles, and handling user authentication. This enhanced user interaction and experience by providing a smooth and intuitive navigation flow throughout the application.