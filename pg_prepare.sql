-- prerequisite
-- CREATE USER accelerator WITH PASSWORD 'accelerator';
-- CREATE SCHEMA AUTHORIZATION accelerator;

CREATE TABLE accelerator.model (
  x REAL,
  y REAL,
  fraud BOOLEAN
);


CREATE TABLE accelerator.live_data (
  x REAL,
  y REAL,
  ts TIMESTAMP
);
CREATE INDEX ON accelerator.live_data (ts);

INSERT INTO accelerator.model VALUES (0, 0, False),
                                     (20, 20, True);