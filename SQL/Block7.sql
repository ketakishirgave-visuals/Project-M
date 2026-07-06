WITH user_totals AS (
    SELECT 
        customer_id,
        SUM(cashback_applied) AS total_user_cashback,
        SUM(net_revenue_rs) AS total_user_profit,
        PERCENT_RANK() OVER (ORDER BY SUM(cashback_applied) DESC) AS cashback_percent_rank
    FROM transactions
    GROUP BY customer_id
)
SELECT 
    CASE WHEN cashback_percent_rank <= 0.10 THEN 'Top 10% Users' ELSE 'Remaining 90% Users' END AS concentration_tier,
    COUNT(*) AS total_users,
    SUM(total_user_cashback) AS total_cashback_consumed,
    SUM(total_user_profit) AS total_profit_yield,
    ROUND(SUM(total_user_cashback) * 100.0 / (SELECT SUM(cashback_applied) FROM transactions), 2) AS cashback_concentration_pct,
    ROUND(SUM(total_user_profit) * 100.0 / (SELECT COALESCE(SUM(net_revenue_rs), 1) FROM transactions), 2) AS profit_concentration_pct
FROM user_totals
GROUP BY CASE WHEN cashback_percent_rank <= 0.10 THEN 'Top 10% Users' ELSE 'Remaining 90% Users' END;