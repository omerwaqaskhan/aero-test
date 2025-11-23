# Database Replication Setup Guide

This guide explains how to set up PostgreSQL replication for high availability and read scaling.

## Overview

Database replication provides:
- **High Availability**: Automatic failover if primary database fails
- **Read Scaling**: Distribute read queries across multiple replicas
- **Backup**: Real-time backup of your data
- **Disaster Recovery**: Quick recovery from data loss

## Architecture

```
Primary (Write) Database
    │
    ├──> Replica 1 (Read)
    ├──> Replica 2 (Read)
    └──> Replica 3 (Backup/Standby)
```

## Setup Options

### Option 1: Streaming Replication (Recommended for Production)

#### 1. Configure Primary Database

Edit `postgresql.conf`:
```conf
wal_level = replica
max_wal_senders = 3
wal_keep_size = 1GB
hot_standby = on
```

Edit `pg_hba.conf`:
```
host    replication     replicator     <replica-ip>/32    md5
```

#### 2. Create Replication User

```sql
CREATE USER replicator WITH REPLICATION PASSWORD 'strong_password';
```

#### 3. Configure Replica Database

On replica server, initialize from primary:
```bash
pg_basebackup -h <primary-host> -D /var/lib/postgresql/data -U replicator -v -P -W
```

Edit `postgresql.conf`:
```conf
hot_standby = on
```

Create `recovery.conf`:
```
standby_mode = 'on'
primary_conninfo = 'host=<primary-host> port=5432 user=replicator password=strong_password'
trigger_file = '/tmp/postgresql.trigger'
```

#### 4. Update Application Configuration

Update `docker-compose.yml`:
```yaml
services:
  postgres-primary:
    image: postgres:15
    environment:
      POSTGRES_REPLICATION_USER: replicator
      POSTGRES_REPLICATION_PASSWORD: ${POSTGRES_REPLICATION_PASSWORD}
    volumes:
      - ./postgresql.conf:/etc/postgresql/postgresql.conf
    command: postgres -c config_file=/etc/postgresql/postgresql.conf

  postgres-replica:
    image: postgres:15
    environment:
      POSTGRES_MASTER_SERVICE_HOST: postgres-primary
      POSTGRES_REPLICATION_USER: replicator
      POSTGRES_REPLICATION_PASSWORD: ${POSTGRES_REPLICATION_PASSWORD}
    depends_on:
      - postgres-primary
```

### Option 2: Logical Replication (For Cross-Version Upgrades)

Useful for:
- Upgrading PostgreSQL versions
- Selective table replication
- Cross-database replication

```sql
-- On primary
CREATE PUBLICATION my_publication FOR ALL TABLES;

-- On replica
CREATE SUBSCRIPTION my_subscription 
  CONNECTION 'host=primary-host dbname=mydb user=replicator password=password'
  PUBLICATION my_publication;
```

### Option 3: Managed Database Services

#### AWS RDS Multi-AZ
- Automatic failover
- Automated backups
- Read replicas in different regions

#### Google Cloud SQL
- High availability configuration
- Read replicas
- Automated backups

#### Azure Database for PostgreSQL
- Flexible server with high availability
- Read replicas
- Point-in-time restore

## Application Code Changes

### Read/Write Splitting

Update `backend/auth_module/infrastructure/db/database.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

# Primary (write) database
write_engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20
)

# Replica (read) database
read_engine = create_engine(
    REPLICA_DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40
)

# Use read replica for queries
def get_read_db():
    return read_engine

# Use primary for writes
def get_write_db():
    return write_engine
```

### Router Pattern

```python
class DatabaseRouter:
    """Route queries to appropriate database."""
    
    def __init__(self):
        self.write_db = get_write_db()
        self.read_db = get_read_db()
    
    def get_session(self, read_only=False):
        """Get database session."""
        if read_only:
            return self.read_db
        return self.write_db

# Usage in routers
@router.get("/hotels")
async def list_hotels(db: Session = Depends(get_read_db)):
    # Read query uses replica
    return db.query(HotelModel).all()

@router.post("/hotels")
async def create_hotel(hotel: HotelCreate, db: Session = Depends(get_write_db)):
    # Write query uses primary
    db_hotel = HotelModel(**hotel.dict())
    db.add(db_hotel)
    db.commit()
    return db_hotel
```

## Monitoring

### Check Replication Status

```sql
-- On primary
SELECT * FROM pg_stat_replication;

-- On replica
SELECT * FROM pg_stat_wal_receiver;
```

### Check Lag

```sql
SELECT 
    client_addr,
    state,
    sync_state,
    pg_wal_lsn_diff(pg_current_wal_lsn(), sent_lsn) AS replication_lag_bytes
FROM pg_stat_replication;
```

## Failover Procedures

### Automatic Failover with Patroni

```yaml
# patroni.yml
scope: aero-hotels
namespace: /db/
name: postgresql0

restapi:
  listen: 0.0.0.0:8008
  connect_address: localhost:8008

bootstrap:
  dcs:
    ttl: 30
    loop_wait: 10
    retry_timeout: 30
    maximum_lag_on_failover: 1048576

postgresql:
  listen: 0.0.0.0:5432
  connect_address: localhost:5432
  data_dir: /var/lib/postgresql/data
  pgpass: /tmp/pgpass
  authentication:
    replication:
      username: replicator
      password: strong_password
    superuser:
      username: postgres
      password: strong_password
```

## Best Practices

1. **Monitor Replication Lag**: Set up alerts for lag > 1 second
2. **Test Failover Regularly**: Monthly failover drills
3. **Backup Strategy**: Combine replication with regular backups
4. **Connection Pooling**: Use PgBouncer or similar
5. **Read Replicas**: Use for analytics and reporting queries
6. **Geographic Distribution**: Place replicas in different regions

## Troubleshooting

### Replication Not Working

1. Check network connectivity
2. Verify `pg_hba.conf` allows replication
3. Check PostgreSQL logs
4. Verify replication user permissions

### High Lag

1. Check network bandwidth
2. Increase `wal_keep_size`
3. Add more replicas to distribute load
4. Optimize slow queries

## References

- [PostgreSQL Replication Documentation](https://www.postgresql.org/docs/current/high-availability.html)
- [Patroni Documentation](https://patroni.readthedocs.io/)
- [PgBouncer Documentation](https://www.pgbouncer.org/)

