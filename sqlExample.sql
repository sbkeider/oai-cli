SELECT account_id
FROM ft_offboard_migration_balances ft
WHERE ft.successor_custodian = 'Disbursement'
AND ft.batch_job_id = '0cc5faeb-28bb-40f2-ab94-f1f12146ce4f'