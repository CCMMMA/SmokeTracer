BEGIN TRANSACTION;

CREATE TABLE "USER" (
    USERNAME TEXT PRIMARY KEY NOT NULL,
    "PASSWORD" TEXT, 
    FIRSTNAME TEXT NOT NULL, 
    LASTNAME TEXT NOT NULL, 
    EMAIL TEXT NOT NULL,
    TELEPHONE TEXT,
    BIRTHDATE TEXT,
    LASTACCESS TEXT,
    STRUTTURA TEXT NOT NULL, 
    RUOLOTEC TEXT NOT NULL,
    ACTIVE INT,
    SEARCH_FIELD TEXT
);

CREATE TABLE GROUPS (
    NAME_GROUP TEXT PRIMARY KEY
);

CREATE TABLE JOBS (
    JOBID TEXT PRIMARY KEY NOT NULL,
    USERNAME TEXT NOT NULL, 
    FOREIGN KEY (USERNAME) REFERENCES "USER" (USERNAME)
);

CREATE TABLE JOBINFO (
    JOBID TEXT PRIMARY KEY NOT NULL,
    NAME_SIM TEXT NOT NULL,
    "DATE" TEXT NOT NULL,
    "TIME" TEXT NOT NULL, 
    DURATION TEXT NOT NULL,
    COMMON TEXT NOT NULL,
    LONG TEXT NOT NULL, 
    LAT TEXT NOT NULL,
    TEMPERATURE TEXT NOT NULL, 
    CODICE_GISA TEXT,
    COMPLETED INT,
    SEARCH_FIELD TEXT, 
    FOREIGN KEY (JOBID) REFERENCES JOBS (JOBID) ON DELETE CASCADE
);

CREATE TABLE USER_GROUP (
    USERNAME TEXT REFERENCES "USER"(USERNAME) ON DELETE CASCADE, 
    NAME_GROUP TEXT REFERENCES GROUPS(NAME_GROUP) ON DELETE CASCADE,
    READ_PERMISSION BOOLEAN NOT NULL,
    WRITE_PERMISSION BOOLEAN, 
    PRIMARY KEY (USERNAME, NAME_GROUP)
);


CREATE TABLE SIMULATION_GROUP (
    JOBID TEXT REFERENCES JOBS(JOBID),
    NAME_GROUP TEXT REFERENCES GROUPS(NAME_GROUP),
    PRIMARY KEY (JOBID, NAME_GROUP)
);


INSERT INTO GROUPS (NAME_GROUP) VALUES ('admin');
INSERT INTO GROUPS (NAME_GROUP) VALUES ('regione_campania');
INSERT INTO GROUPS (NAME_GROUP) VALUES ('izsm');
INSERT INTO GROUPS (NAME_GROUP) VALUES ('asl_avellino');
INSERT INTO GROUPS (NAME_GROUP) VALUES ('asl_benevento');
INSERT INTO GROUPS (NAME_GROUP) VALUES ('asl_caserta');
INSERT INTO GROUPS (NAME_GROUP) VALUES ('asl_napoli_centro');
INSERT INTO GROUPS (NAME_GROUP) VALUES ('asl_napoli_nord');
INSERT INTO GROUPS (NAME_GROUP) VALUES ('asl_napoli_sud');

INSERT INTO "USER" (USERNAME, "PASSWORD", FIRSTNAME, LASTNAME, EMAIL, TELEPHONE, BIRTHDATE, LASTACCESS, STRUTTURA, RUOLOTEC, ACTIVE) VALUES ('superuser', 'pbkdf2:sha256:260000$9TWmqDomDHCZO8B3$19cef8898494e2b04e9b970aadb037bd09ffa30680cf6291223a8466d02c8367', 'SuperUtente', 'UtenteSuper', 'test@example.com', '123456789', '1990-01-01', '2022-01-01', 'Regione Campania', 'Amministrazione', 1);
INSERT INTO USER_GROUP (USERNAME, NAME_GROUP, READ_PERMISSION, WRITE_PERMISSION) VALUES ('superuser', 'admin', TRUE, TRUE);

CREATE EXTENSION postgis;

COMMIT;