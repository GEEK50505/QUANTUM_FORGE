#!/usr/bin/env python3
from backend.app.db.supabase_client import get_supabase_client

client = get_supabase_client()

print('data_quality_metrics latest:')
for r in client.get('data_quality_metrics', select='*', order_by='id.desc', limit=5):
    print(r)

print('\ndata_lineage latest:')
for r in client.get('data_lineage', select='*', order_by='id.desc', limit=5):
    print(r)

print('\nmolecules latest:')
for r in client.get('molecules', select='*', order_by='id.desc', limit=5):
    print(r)

print('\ncalculations latest:')
for r in client.get('calculations', select='*', order_by='id.desc', limit=5):
    print(r)
