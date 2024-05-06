CREATE TABLE users (
    user_id serial PRIMARY KEY,
    username TEXT NOT NULL UNIQUE
);

CREATE TABLE exercises (
    exercise_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    pushups INT,
    pull_ups INT,
    exercise_date DATE,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);