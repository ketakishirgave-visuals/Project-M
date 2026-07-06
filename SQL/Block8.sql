SELECT      
    f.final_cluster_id,     
    ROUND(
        (COUNT(*) * SUM(t.wallet_at_checkout * t.order_value_rs) - SUM(t.wallet_at_checkout) * SUM(t.order_value_rs)) / 
        NULLIF(
            SQRT(
                (COUNT(*) * SUM(t.wallet_at_checkout * t.wallet_at_checkout) - POW(SUM(t.wallet_at_checkout), 2)) * 
                (COUNT(*) * SUM(t.order_value_rs * t.order_value_rs) - POW(SUM(t.order_value_rs), 2))
            ), 
            0
        ), 
        4
    ) AS transaction_level_pearson_r 
FROM transactions t     
JOIN final_cluster_assignments f ON t.customer_id = f.customer_id 
GROUP BY f.final_cluster_id 
ORDER BY f.final_cluster_id;

