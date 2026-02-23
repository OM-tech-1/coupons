#!/usr/bin/env python3
"""
Query database directly to check payment and webhook status.

Usage:
  python3 scripts/query_payment_status.py
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from sqlalchemy import text


def run_query(db, query, title):
    """Run a query and display results"""
    print("=" * 80)
    print(title)
    print("=" * 80)
    
    result = db.execute(text(query))
    rows = result.fetchall()
    
    if not rows:
        print("No results found.")
        print()
        return
    
    # Get column names
    columns = result.keys()
    
    # Print header
    header = " | ".join(str(col)[:20].ljust(20) for col in columns)
    print(header)
    print("-" * len(header))
    
    # Print rows
    for row in rows:
        row_str = " | ".join(str(val)[:20].ljust(20) if val is not None else "NULL".ljust(20) for val in row)
        print(row_str)
    
    print()


def main():
    db = SessionLocal()
    
    try:
        # Query 1: Recent Payments
        run_query(db, """
            SELECT 
                id,
                stripe_payment_intent_id,
                status,
                amount,
                currency,
                created_at,
                completed_at
            FROM payments
            ORDER BY created_at DESC
            LIMIT 5
        """, "RECENT PAYMENTS")
        
        # Query 2: Pending Payments
        run_query(db, """
            SELECT 
                p.id,
                p.stripe_payment_intent_id,
                p.status,
                p.created_at,
                o.status as order_status
            FROM payments p
            LEFT JOIN orders o ON o.id = p.order_id
            WHERE p.status = 'pending'
            ORDER BY p.created_at DESC
            LIMIT 5
        """, "PENDING PAYMENTS (Waiting for Webhook)")
        
        # Query 3: Succeeded Payments
        run_query(db, """
            SELECT 
                p.id,
                p.stripe_payment_intent_id,
                p.status,
                p.completed_at,
                o.status as order_status
            FROM payments p
            LEFT JOIN orders o ON o.id = p.order_id
            WHERE p.status = 'succeeded'
            ORDER BY p.created_at DESC
            LIMIT 5
        """, "SUCCEEDED PAYMENTS (Webhook Received)")
        
        # Query 4: Orders with Payment Status
        run_query(db, """
            SELECT 
                o.id,
                o.status as order_status,
                o.payment_state,
                o.total_amount,
                p.status as payment_status,
                p.stripe_payment_intent_id
            FROM orders o
            LEFT JOIN payments p ON p.order_id = o.id
            ORDER BY o.created_at DESC
            LIMIT 5
        """, "ORDERS WITH PAYMENT STATUS")
        
        # Query 5: Summary Statistics
        run_query(db, """
            SELECT 
                'Total Payments' as metric,
                COUNT(*) as count
            FROM payments
            UNION ALL
            SELECT 
                'Pending Payments',
                COUNT(*)
            FROM payments
            WHERE status = 'pending'
            UNION ALL
            SELECT 
                'Succeeded Payments',
                COUNT(*)
            FROM payments
            WHERE status = 'succeeded'
            UNION ALL
            SELECT 
                'Failed Payments',
                COUNT(*)
            FROM payments
            WHERE status = 'failed'
            UNION ALL
            SELECT 
                'Orders Paid',
                COUNT(*)
            FROM orders
            WHERE status = 'paid'
            UNION ALL
            SELECT 
                'Orders Pending',
                COUNT(*)
            FROM orders
            WHERE status = 'pending_payment'
        """, "SUMMARY STATISTICS")
        
        print("=" * 80)
        print("WHAT TO LOOK FOR:")
        print("=" * 80)
        print()
        print("✓ Webhook Working:")
        print("  - Payment status changes from 'pending' to 'succeeded'")
        print("  - Order status changes from 'pending_payment' to 'paid'")
        print("  - completed_at timestamp is set")
        print("  - Few or no 'pending' payments")
        print()
        print("✗ Webhook NOT Working:")
        print("  - Many payments stuck in 'pending' status")
        print("  - Orders stuck in 'pending_payment' status")
        print("  - completed_at is NULL")
        print()
        
    except Exception as e:
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
