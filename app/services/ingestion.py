from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import HealthObservation, MetricDefinition, DataSource, User
from app.schemas import BatchIngestRequest
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

class IngestionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.metric_map = {} # Cache: {"HEALX_TEST_TOTAL": 101, ...}

    async def _load_metric_map(self):
        """
        Fetches all metric definitions into a dictionary for O(1) lookup.
        In production, cache this in Redis or memory with a TTL.
        """
        result = await self.db.execute(select(MetricDefinition.id, MetricDefinition.code))
        rows = result.all()
        # Create map: code -> id
        self.metric_map = {row.code: row.id for row in rows}
        logger.info(f"Loaded {len(self.metric_map)} metrics into cache.")

    async def _get_or_create_source(self, source_name: str) -> int:
        # Simple lookup for source ID. 
        # In high throughput, sources are few, so we can query or cache.
        result = await self.db.execute(select(DataSource).where(DataSource.name == source_name))
        source = result.scalars().first()
        if source:
            return source.id
        
        # Create if not exists (simplistic approach, watch for race conditions in distributed env)
        new_source = DataSource(name=source_name, is_trusted=False)
        self.db.add(new_source)
        await self.db.flush() # Get ID without committing transaction
        return new_source.id

    async def process_batch(self, user_id: str, batch: BatchIngestRequest):
        # 0. Validate User (Optional if constraints require it)
        # Ensure user exists logic could go here, or let FK constraint fail.
        
        # 1. Ensure our map is loaded
        if not self.metric_map:
            await self._load_metric_map()
        
        source_id = await self._get_or_create_source(batch.source_name)
        
        observations_to_insert = []
        unknown_metrics = []

        # 2. Iterate line-by-line (in memory)
        for item in batch.data:
            metric_id = self.metric_map.get(item.metric_code)
            
            if not metric_id:
                # Handle unknown metrics (Log them, or skip)
                unknown_metrics.append(item.metric_code)
                continue

            # 3. Build the DB Object
            obs = HealthObservation(
                user_id=user_id,
                metric_id=metric_id,
                source_id=source_id,
                recorded_at=item.recorded_at,
                value_numeric=item.value_numeric,
                value_text=item.value_text,
                raw_metadata=item.raw_metadata
            )
            observations_to_insert.append(obs)

        # 4. Bulk Insert (Single Transaction)
        if observations_to_insert:
            self.db.add_all(observations_to_insert)
            try:
                await self.db.commit() # Commits all 50 or 5,000 rows at once
            except Exception as e:
                await self.db.rollback()
                logger.error(f"Batch insert failed: {e}")
                raise HTTPException(status_code=500, detail="Batch insert failed")

        return {
            "processed": len(observations_to_insert),
            "skipped_unknown_metrics": list(set(unknown_metrics)), # Deduplicate
            "source_id": source_id
        }
