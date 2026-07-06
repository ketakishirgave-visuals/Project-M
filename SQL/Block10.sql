WITH wallet_history AS (
    SELECT 
        customer_id,
        purchase_day, -- or transaction_date / week_id depending on grain
        wallet_at_checkout,
        order_value_rs,
        -- Tracks the maximum wallet balance this user had EVER seen PRIOR to this transaction
        MAX(wallet_at_checkout) OVER (
            PARTITION BY customer_id 
            ORDER BY purchase_day 
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ) AS historic_peak_wallet
    FROM transactions
),
post_peak_conversions AS (
    SELECT 
        *,
        CASE 
            WHEN historic_peak_wallet IS NULL THEN 'Pre-Peak Baseline'
            WHEN wallet_at_checkout >= historic_peak_wallet THEN 'At/Above Historic Peak'
            WHEN wallet_at_checkout < historic_peak_wallet THEN 'Accepting Lower Amounts (₹10-40)'
            ELSE 'Other'
        END AS checkout_behavior_tier
    FROM wallet_history
)
SELECT 
    checkout_behavior_tier,
    COUNT(*) AS total_orders_placed,
    ROUND(AVG(wallet_at_checkout), 2) AS avg_wallet_at_checkout,
    ROUND(AVG(order_value_rs), 2) AS avg_basket_size
FROM post_peak_conversions
GROUP BY 1 
ORDER BY total_orders_placed DESC;