import csv
import json
import logging
import os
from datetime import datetime, timezone

from celery import shared_task
from django.conf import settings

logger = logging.getLogger("apps.storage")


@shared_task(bind=True, max_retries=2, default_retry_delay=10)
def process_submit_job(self, job_id):
    """
    Background task: write back to source DB, export file, update job status.
    """
    from apps.connections.connectors.factory import ConnectorFactory
    from .models import SubmitJob, ProcessedDataRecord, ExportedFile

    try:
        job = SubmitJob.objects.select_related("connection", "user").get(id=job_id)
    except SubmitJob.DoesNotExist:
        logger.error("action=submit_task job_id=%s result=job_not_found", job_id)
        return

    job.status = "running"
    job.save(update_fields=["status"])

    config = job.connection
    user = job.user

    try:
        # The data and original_data are stored on the ProcessedDataRecord
        record = job.record
        data = record.data
        table_name = job.table_name
        export_format = job.export_format

        # 1. Write changes back to the source database
        rows_updated = 0
        source_update_error = ""
        try:
            connector = ConnectorFactory.from_config(config)
            with connector:
                original_data = getattr(record, "_original_data", [])
                rows_updated = connector.update_rows(table_name, data, original_data)
        except Exception as e:
            source_update_error = str(e)
            logger.error(
                "action=submit_task_writeback job_id=%s connection_id=%s table=%s result=failed",
                job.id, config.id, table_name,
            )

        # 2. Export as file
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        file_name = f"{table_name}_{config.db_type}_{timestamp}.{export_format}"

        exports_dir = settings.EXPORTS_DIR
        os.makedirs(exports_dir, exist_ok=True)
        file_path = os.path.join(str(exports_dir), file_name)

        metadata = {
            "source_db_type": config.db_type,
            "source_table": table_name,
            "connection_name": config.name,
            "exported_by": user.username,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "row_count": len(data),
        }

        if export_format == "json":
            output = {"metadata": metadata, "data": data}
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=2, default=str)
        else:  # csv
            if data:
                with open(file_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=data[0].keys())
                    writer.writeheader()
                    writer.writerows(data)

        exported_file = ExportedFile.objects.create(
            user=user,
            processed_record=record,
            file_format=export_format,
            file_path=file_path,
            file_name=file_name,
            source_db_type=config.db_type,
            source_table=table_name,
        )

        # 3. Update job as completed
        job.exported_file = exported_file
        job.rows_updated_in_source = rows_updated
        job.source_update_error = source_update_error
        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)
        job.save()

        logger.info(
            "action=submit_task job_id=%s user_id=%s connection_id=%s table=%s rows=%d "
            "format=%s file_id=%s rows_updated=%d status=completed",
            job.id, user.id, config.id, table_name, len(data),
            export_format, exported_file.id, rows_updated,
        )

    except Exception as exc:
        job.status = "failed"
        job.error_message = str(exc)
        job.completed_at = datetime.now(timezone.utc)
        job.save()

        logger.error(
            "action=submit_task job_id=%s user_id=%s status=failed error_type=%s",
            job.id, job.user_id, type(exc).__name__,
        )
