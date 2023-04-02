DROP DATABASE page_analyzer IF EXISTS;

CREATE TABLE urls (
    id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name varchar(255) UNIQUE NOT NULL,
    created_at timestamp NOT NULL
);

CREATE TABLE url_checks (
    id bigint PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    url_id bigint REFERENCES urls(id),
    status_code integer NOT NULL,
    h1 varchar(255),
    title varchar(255),
    description varchar(255),
    created_at timestamp NOT NULL
);