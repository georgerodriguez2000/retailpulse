from src.loading.postgres import get_connection


def start_pipeline_run(pipeline_name):
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO pipeline_runs (
                pipeline_name,
                status
            )
            VALUES (%s, %s)
            RETURNING run_id;
            """,
            (
                pipeline_name,
                "RUNNING"
            )
        )

        run_id = cursor.fetchone()[0]

    connection.commit()
    connection.close()

    return run_id

def finish_pipeline_run(
    run_id,
    status,
    rows_extracted,
    rows_valid,
    rows_rejected,
    rows_loaded,
    raw_file,
    clean_file,
    rejected_file=None,
    error_message=None
):
    connection = get_connection()

    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE pipeline_runs
            SET
                finished_at = CURRENT_TIMESTAMP,
                status = %s,
                rows_extracted = %s,
                rows_valid = %s,
                rows_rejected = %s,
                rows_loaded = %s,
                raw_file = %s,
                clean_file = %s,
                rejected_file = %s,
                error_message = %s
            WHERE run_id = %s;
            """,
            (
                status,
                rows_extracted,
                rows_valid,
                rows_rejected,
                rows_loaded,
                str(raw_file) if raw_file else None,
                str(clean_file) if clean_file else None,
                str(rejected_file) if rejected_file else None,
                error_message,
                run_id
            )
        )

    connection.commit()
    connection.close()


if __name__ == "__main__":
    finish_pipeline_run(
        run_id=1,
        status="SUCCESS",
        rows_extracted=194,
        rows_valid=194,
        rows_rejected=0,
        rows_loaded=194,
        raw_file="data/raw/products/test.json",
        clean_file="data/clean/products/test.json"
    )

    print("Pipeline run finalizado.")