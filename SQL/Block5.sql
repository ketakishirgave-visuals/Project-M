SELECT 
    f.final_cluster_id,
    CASE 
        WHEN t.purchase_day <= 3 THEN 'Early Window (Days 1-3)'
        WHEN t.purchase_day >= 5 THEN 'Expiry Pressure (Days 5-7)'
        ELSE 'Mid-lifecycle (Day 4)'
    END AS purchase_timing_window,
    COUNT(*) AS total_orders,
    AVG(t.wallet_at_checkout) AS wallet_at_checkout_trigger,
    AVG(t.order_value_rs) AS average_order_value
FROM transactions t
JOIN final_cluster_assignments f ON t.customer_id = f.customer_id
GROUP BY f.final_cluster_id, 
         CASE 
             WHEN t.purchase_day <= 3 THEN 'Early Window (Days 1-3)'
             WHEN t.purchase_day >= 5 THEN 'Expiry Pressure (Days 5-7)'
             ELSE 'Mid-lifecycle (Day 4)'
         END
ORDER BY f.final_cluster_id, purchase_timing_window;