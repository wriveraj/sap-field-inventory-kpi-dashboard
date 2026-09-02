-- SAP Field Inventory KPI Dashboard — synthetic schema
-- Models a surgical device field-inventory territory: PAR levels, case demand,
-- advanced allocations, and cycle counts. All data is synthetic — no employer
-- data, account numbers, or real site names are used anywhere in this project.

CREATE TABLE territories (
    territory_id    SERIAL PRIMARY KEY,
    territory_name  VARCHAR(50) NOT NULL,
    region          VARCHAR(50) NOT NULL
);

CREATE TABLE sites (
    site_id         SERIAL PRIMARY KEY,
    site_name       VARCHAR(100) NOT NULL,
    territory_id    INTEGER NOT NULL REFERENCES territories(territory_id),
    site_type       VARCHAR(20) NOT NULL,   -- Hospital, ASC, Clinic
    state           VARCHAR(2) NOT NULL
);

CREATE TABLE products (
    product_id      SERIAL PRIMARY KEY,
    product_name    VARCHAR(100) NOT NULL,
    category        VARCHAR(30) NOT NULL,   -- Implant, Instrument, Disposable, PPE
    unit_cost       NUMERIC(10,2) NOT NULL
);

CREATE TABLE par_levels (
    par_id              SERIAL PRIMARY KEY,
    site_id             INTEGER NOT NULL REFERENCES sites(site_id),
    product_id          INTEGER NOT NULL REFERENCES products(product_id),
    par_qty             INTEGER NOT NULL,
    effective_start_date DATE NOT NULL,
    effective_end_date   DATE            -- NULL = currently active
);

CREATE TABLE inventory_snapshots (
    snapshot_id     SERIAL PRIMARY KEY,
    site_id         INTEGER NOT NULL REFERENCES sites(site_id),
    product_id      INTEGER NOT NULL REFERENCES products(product_id),
    snapshot_date   DATE NOT NULL,
    on_hand_qty     INTEGER NOT NULL
);

CREATE TABLE cases (
    case_id         SERIAL PRIMARY KEY,
    site_id         INTEGER NOT NULL REFERENCES sites(site_id),
    product_id      INTEGER NOT NULL REFERENCES products(product_id),
    case_date       DATE NOT NULL,
    qty_required    INTEGER NOT NULL,
    case_status     VARCHAR(20) NOT NULL   -- Fulfilled, Delayed, Cancelled
);

CREATE TABLE allocations (
    allocation_id       SERIAL PRIMARY KEY,
    destination_site_id INTEGER NOT NULL REFERENCES sites(site_id),
    product_id           INTEGER NOT NULL REFERENCES products(product_id),
    qty                   INTEGER NOT NULL,
    request_date          DATE NOT NULL,
    fulfilled_date        DATE            -- NULL = still open
);

CREATE TABLE cycle_counts (
    count_id        SERIAL PRIMARY KEY,
    site_id         INTEGER NOT NULL REFERENCES sites(site_id),
    product_id      INTEGER NOT NULL REFERENCES products(product_id),
    count_date      DATE NOT NULL,
    expected_qty    INTEGER NOT NULL,
    actual_qty      INTEGER NOT NULL
);

CREATE TABLE demand_history (
    demand_id       SERIAL PRIMARY KEY,
    site_id         INTEGER NOT NULL REFERENCES sites(site_id),
    product_id      INTEGER NOT NULL REFERENCES products(product_id),
    usage_month     DATE NOT NULL,          -- first of month
    qty_used        INTEGER NOT NULL
);

CREATE INDEX idx_par_site_product ON par_levels(site_id, product_id);
CREATE INDEX idx_snapshot_site_date ON inventory_snapshots(site_id, snapshot_date);
CREATE INDEX idx_cases_site_date ON cases(site_id, case_date);
CREATE INDEX idx_allocations_dest ON allocations(destination_site_id);
CREATE INDEX idx_demand_site_month ON demand_history(site_id, usage_month);
