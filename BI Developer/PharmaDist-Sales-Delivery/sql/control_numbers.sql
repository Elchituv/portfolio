/* =====================================================================
   PharmaDist - control numbers for the Power BI report
   ---------------------------------------------------------------------
   Rebuilds the Power Query cleaning and the DAX logic in plain SQL, so
   every number on the dashboard can be checked against an independent
   calculation.
   Dialect : DuckDB (reads the CSV files directly, no database needed).
             Run from the project folder:  duckdb < sql/control_numbers.sql
   Data    : orders 01/01/2024 - 30/09/2026 (ERP extract date 30/09/2026)
   ===================================================================== */

/* 1. DATA-QUALITY PROFILE - what Power Query has to fix --------------- */
SELECT 'OrderLines: rows in file'                     AS check_name, COUNT(*) AS n FROM read_csv('data/OrderLines.csv')
UNION ALL
SELECT 'OrderLines: exact duplicate rows',
       COUNT(*) - (SELECT COUNT(*) FROM (SELECT DISTINCT * FROM read_csv('data/OrderLines.csv'))) FROM read_csv('data/OrderLines.csv')
UNION ALL
SELECT 'OrderLines: zero-quantity rows (after de-dup)',
       COUNT(*) FROM (SELECT DISTINCT * FROM read_csv('data/OrderLines.csv')) WHERE Quantity = 0
UNION ALL
SELECT 'Orders: CustomerID lower-case or padded',     COUNT(*) FROM read_csv('data/Orders.csv') WHERE CustomerID <> UPPER(TRIM(CustomerID))
UNION ALL
SELECT 'Customers: Region spellings in file',         COUNT(DISTINCT Region) FROM read_csv('data/Customers.csv')
UNION ALL
SELECT 'Products: empty Category',                    COUNT(*) FROM read_csv('data/Products.csv', all_varchar = true) WHERE COALESCE(TRIM(Category), '') = '';

/* 2. CLEAN MODEL - mirrors the Power Query steps ---------------------- */
CREATE OR REPLACE VIEW customers AS
SELECT CustomerID, CustomerName, CustomerType,
       UPPER(TRIM(Region)[1]) || LOWER(TRIM(Region)[2:]) AS Region
FROM read_csv('data/Customers.csv');

CREATE OR REPLACE VIEW products AS
SELECT ProductID, ProductName,
       CASE WHEN COALESCE(TRIM(Category), '') = '' THEN 'Unclassified' ELSE Category END AS Category,
       CAST(StandardCost AS DOUBLE) AS StandardCost
FROM read_csv('data/Products.csv', all_varchar = true);

CREATE OR REPLACE VIEW sales AS
WITH lines AS (
    SELECT DISTINCT * FROM read_csv('data/OrderLines.csv')          -- Remove duplicates
)
SELECT
    l.OrderID, l.LineNo, l.ProductID, l.Quantity, l.QtyDelivered, l.UnitPrice, l.DiscountPct,
    UPPER(TRIM(o.CustomerID))                                       AS CustomerID,
    o.OrderDate, o.RequestedDeliveryDate, o.ActualDeliveryDate, o.OrderStatus,
    l.QtyDelivered * l.UnitPrice * (1 - l.DiscountPct)             AS NetAmount,
    CASE WHEN o.OrderStatus = 'Delivered'
          AND o.ActualDeliveryDate <= o.RequestedDeliveryDate THEN 1 ELSE 0 END AS OnTime,
    CASE WHEN l.QtyDelivered >= l.Quantity THEN 1 ELSE 0 END        AS LineInFull
FROM lines l
LEFT JOIN read_csv('data/Orders.csv') o USING (OrderID)             -- Merge queries
WHERE l.Quantity > 0;                                               -- filter zero-quantity lines

/* 3. CONTROL NUMBERS ---------------------------------------------------- */

-- 3.1 Net sales, gross margin %, delivered orders by year      (DAX: [Net Sales], [Gross Margin %], [Orders])
SELECT
    YEAR(s.OrderDate)                                               AS year,
    ROUND(SUM(s.NetAmount), 0)                                      AS net_sales,
    ROUND(100 * SUM(s.NetAmount - s.QtyDelivered * p.StandardCost) / SUM(s.NetAmount), 1) AS gross_margin_pct,
    COUNT(DISTINCT s.OrderID) FILTER (WHERE s.OrderStatus = 'Delivered') AS orders
FROM sales s JOIN products p USING (ProductID)
GROUP BY ALL ORDER BY year;

-- 3.2 2026 (Jan-Sep) vs same period 2025                      (DAX: [Net Sales LY], [YoY %])
SELECT
    ROUND(SUM(NetAmount) FILTER (WHERE OrderDate BETWEEN '2026-01-01' AND '2026-09-30'), 0) AS net_sales_2026,
    ROUND(SUM(NetAmount) FILTER (WHERE OrderDate BETWEEN '2025-01-01' AND '2025-09-30'), 0) AS net_sales_ly,
    ROUND(100 * (SUM(NetAmount) FILTER (WHERE OrderDate BETWEEN '2026-01-01' AND '2026-09-30')
               / SUM(NetAmount) FILTER (WHERE OrderDate BETWEEN '2025-01-01' AND '2025-09-30') - 1), 1) AS yoy_pct
FROM sales;

-- 3.3 Monthly trend with same month last year (window function LAG)
WITH m AS (
    SELECT DATE_TRUNC('month', OrderDate) AS month_start, SUM(NetAmount) AS net_sales
    FROM sales GROUP BY ALL
)
SELECT strftime(month_start, '%Y-%m')                                AS month,
       ROUND(net_sales, 0)                                           AS net_sales,
       ROUND(LAG(net_sales, 12) OVER (ORDER BY month_start), 0)      AS same_month_ly,
       ROUND(100 * (net_sales / LAG(net_sales, 12) OVER (ORDER BY month_start) - 1), 1) AS yoy_pct
FROM m ORDER BY month_start DESC LIMIT 12;

-- 3.4 Category growth, Jan-Sep 2026 vs Jan-Sep 2025
SELECT p.Category,
       ROUND(SUM(s.NetAmount) FILTER (WHERE s.OrderDate BETWEEN '2026-01-01' AND '2026-09-30'), 0) AS net_sales_2026,
       ROUND(100 * (SUM(s.NetAmount) FILTER (WHERE s.OrderDate BETWEEN '2026-01-01' AND '2026-09-30')
                  / SUM(s.NetAmount) FILTER (WHERE s.OrderDate BETWEEN '2025-01-01' AND '2025-09-30') - 1), 1) AS yoy_pct
FROM sales s JOIN products p USING (ProductID)
GROUP BY ALL ORDER BY net_sales_2026 DESC;

-- 3.5 Customer concentration 2025: rank and cumulative share (Pareto)
WITH c AS (
    SELECT cu.CustomerName, cu.CustomerType, SUM(s.NetAmount) AS net_sales
    FROM sales s JOIN customers cu USING (CustomerID)
    WHERE YEAR(s.OrderDate) = 2025 GROUP BY ALL
)
SELECT RANK() OVER (ORDER BY net_sales DESC)                         AS rnk,
       CustomerName, CustomerType, ROUND(net_sales, 0)               AS net_sales,
       ROUND(100 * SUM(net_sales) OVER (ORDER BY net_sales DESC ROWS UNBOUNDED PRECEDING)
                 / SUM(net_sales) OVER (), 1)                        AS cumulative_share_pct
FROM c QUALIFY rnk <= 10 ORDER BY rnk;

-- 3.6 OTIF by region, 2026                                     (DAX: [On-Time %], [In-Full %], [OTIF %])
WITH orders AS (
    SELECT OrderID, ANY_VALUE(CustomerID) AS CustomerID,
           MIN(OnTime) AS on_time, MIN(LineInFull) AS in_full
    FROM sales
    WHERE OrderStatus = 'Delivered' AND YEAR(OrderDate) = 2026
    GROUP BY OrderID
)
SELECT COALESCE(cu.Region, 'ALL REGIONS')                            AS region,
       COUNT(*)                                                      AS orders,
       ROUND(100 * AVG(on_time), 1)                                  AS on_time_pct,
       ROUND(100 * AVG(in_full), 1)                                  AS in_full_pct,
       ROUND(100 * AVG(on_time * in_full), 1)                        AS otif_pct
FROM orders o JOIN customers cu USING (CustomerID)
GROUP BY ROLLUP (cu.Region) ORDER BY cu.Region NULLS FIRST;
