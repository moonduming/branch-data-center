-- 分润指标规则初始化脚本
-- 来源：
-- 1. scripts/new_point.sql
-- 2. scripts/new_daily_avg.sql
-- 3. perf_indicator_rule 当前生效版本公共配置

INSERT INTO `perf_indicator_rule_post_profit`
(`id`, `indicator_id`, `rule_version`, `is_current`, `rule_name`, `point_sql_template`, `daily_avg_sql_template`, `calc_mode`, `result_fields`, `org_prefix`, `need_org_filter`, `need_date_param`, `need_day_count_param`, `run_mode`, `data_source_desc`, `display_value_field`, `compare_value_field`, `status`, `remark`)
SELECT
    r.id,
    r.indicator_id,
    r.rule_version,
    r.is_current,
    r.rule_name,
    CASE r.indicator_id
        WHEN 2 THEN 'WITH base_indicator AS (
    SELECT
        ORIG_ACCT_ID,
        RIGHT(MNG_ORG_ID, 8) AS org_id,
        CUR_BAL AS metric_value_2,
        DATA_DT
    FROM shenzhen_data.i01_sz_acct_sum_d_history
    WHERE DATA_DT = ''{data_dt}''
      AND SUBSTR(MNG_ACCNT_PROD_ID, 1, 4) = ''L120''
      AND CCY_CD IN (''156'', ''B02'')
      AND (''{org_id}'' = '''' OR RIGHT(MNG_ORG_ID, 8) = ''{org_id}'')
),
latest_time AS (
    SELECT
        ORIG_ACCT_ID,
        MAX(DATA_DT) AS max_data_dt
    FROM shenzhen_data.shenzhen_prop_status
    WHERE DATA_DT <= (SELECT MAX(DATA_DT) FROM base_indicator)
      AND PROP_STATUS_FLG = ''1''
      AND ORIG_ACCT_ID IN (
          SELECT DISTINCT ORIG_ACCT_ID
          FROM base_indicator
          WHERE ORIG_ACCT_ID IS NOT NULL
      )
    GROUP BY ORIG_ACCT_ID
),
valid_ratio AS (
    SELECT
        pb.ORIG_ACCT_ID,
        pb.ACCOUNTING_ORG_ID,
        pb.employee_no,
        pb.employee_name,
        pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ORIG_ACCT_ID = lt.ORIG_ACCT_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCOUNTING_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ORIG_ACCT_ID = vr.ORIG_ACCT_ID
GROUP BY vr.ACCOUNTING_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;'
        WHEN 3 THEN 'WITH base_indicator AS (
    SELECT
        P1.ORIG_ACCT_ID,
        P1.ACCNT_ORG_ID AS org_id,
        CASE
            WHEN P1.MNG_ACCNT_PROD_ID LIKE ''L11002%'' OR P1.MNG_ACCNT_PROD_ID LIKE ''L12002%'' THEN P1.CUR_BAL
            WHEN (P1.MNG_ACCNT_PROD_ID LIKE ''L11001%'' OR P1.MNG_ACCNT_PROD_ID LIKE ''L12001%'')
                 AND CAST(P1.ACCT_TERM AS DECIMAL(18, 4)) <= 730 THEN P1.CUR_BAL
            WHEN (P1.MNG_ACCNT_PROD_ID LIKE ''L11001%'' OR P1.MNG_ACCNT_PROD_ID LIKE ''L12001%'')
                 AND CAST(P1.ACCT_TERM AS DECIMAL(18, 4)) > 730
                 AND P1.EXEC_RATE <= P4.PARA_SCOPE THEN P1.CUR_BAL
            ELSE 0
        END AS metric_value_2,
        P1.DATA_DT
    FROM shenzhen_data.i01_sz_acct_sum_d_history P1
    LEFT JOIN shenzhen_data.FDL_REFL_DIM_PARAMET_CONFIG P4
        ON (CASE
                WHEN SUBSTR(P1.MNG_ACCNT_PROD_ID, 1, 6) = ''L12001'' THEN ''CORP_DEP_RT''
                WHEN SUBSTR(P1.MNG_ACCNT_PROD_ID, 1, 6) = ''L11001'' THEN ''INDIV_DEP_RT''
                ELSE ''''
            END) = P4.DIM_CD
       AND P1.INT_ST_DT >= CAST(P4.PARA_ST_VAL AS DATE)
       AND P1.INT_ST_DT < CAST(P4.PARA_END_VAL AS DATE)
       AND (CASE
                WHEN CAST(P1.ACCT_TERM AS DECIMAL(18, 4)) > 730 THEN ''3Y''
                ELSE ''''
            END) = P4.PARA_CD
       AND P4.YEAR = SUBSTR(''{data_dt}'', 1, 4)
       AND P4.BIZ_TYPE_CD = ''B_DP_RT''
    WHERE P1.DATA_DT = ''{data_dt}''
      AND P1.BASIS_CD IN (''D_100'')
      AND P1.CCY_CD IN (''156'', ''B02'')
      AND SUBSTR(P1.MNG_ACCNT_PROD_ID, 1, 4) = ''L120''
      AND (''{org_id}'' = '''' OR P1.ACCNT_ORG_ID = ''{org_id}'')
),
latest_time AS (
    SELECT ORIG_ACCT_ID, MAX(DATA_DT) AS max_data_dt
    FROM shenzhen_data.shenzhen_prop_status
    WHERE DATA_DT <= (SELECT MAX(DATA_DT) FROM base_indicator)
      AND PROP_STATUS_FLG = ''1''
      AND ORIG_ACCT_ID IN (SELECT DISTINCT ORIG_ACCT_ID FROM base_indicator WHERE ORIG_ACCT_ID IS NOT NULL)
    GROUP BY ORIG_ACCT_ID
),
valid_ratio AS (
    SELECT pb.ORIG_ACCT_ID, pb.ACCOUNTING_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ORIG_ACCT_ID = lt.ORIG_ACCT_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCOUNTING_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ORIG_ACCT_ID = vr.ORIG_ACCT_ID
GROUP BY vr.ACCOUNTING_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;'
        WHEN 4 THEN 'WITH base_indicator AS (
    SELECT
        ORIG_ACCT_ID,
        RIGHT(MNG_ORG_ID, 8) AS org_id,
        CUR_BAL AS metric_value_2,
        DATA_DT
    FROM shenzhen_data.i01_sz_acct_sum_d_history
    WHERE DATA_DT = ''{data_dt}''
      AND SUBSTR(MNG_ACCNT_PROD_ID, 1, 4) = ''L120''
      AND CCY_CD IN (''156'', ''B02'')
      AND FIX_CUR_FLG = ''0''
      AND (''{org_id}'' = '''' OR RIGHT(MNG_ORG_ID, 8) = ''{org_id}'')
),
latest_time AS (
    SELECT ORIG_ACCT_ID, MAX(DATA_DT) AS max_data_dt
    FROM shenzhen_data.shenzhen_prop_status
    WHERE DATA_DT <= (SELECT MAX(DATA_DT) FROM base_indicator)
      AND PROP_STATUS_FLG = ''1''
      AND ORIG_ACCT_ID IN (SELECT DISTINCT ORIG_ACCT_ID FROM base_indicator WHERE ORIG_ACCT_ID IS NOT NULL)
    GROUP BY ORIG_ACCT_ID
),
valid_ratio AS (
    SELECT pb.ORIG_ACCT_ID, pb.ACCOUNTING_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ORIG_ACCT_ID = lt.ORIG_ACCT_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCOUNTING_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ORIG_ACCT_ID = vr.ORIG_ACCT_ID
GROUP BY vr.ACCOUNTING_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;'
        WHEN 5 THEN 'WITH base_indicator AS (
    SELECT
        ECIF_CUST_ID,
        RIGHT(MNG_ORG_ID, 8) AS org_id,
        CUR_BAL AS metric_value_2,
        DATA_DT
    FROM shenzhen_data.i01_sz_acct_sum_d_history
    WHERE DATA_DT = ''{data_dt}''
      AND SUBSTR(MNG_ACCNT_PROD_ID, 1, 4) = ''L110''
      AND CCY_CD IN (''156'', ''B02'')
      AND (''{org_id}'' = '''' OR RIGHT(MNG_ORG_ID, 8) = ''{org_id}'')
),
latest_time AS (
    SELECT ECIF_CUST_ID, MAX(DATA_DT) AS max_data_dt
    FROM shenzhen_data.shenzhen_prop_status
    WHERE DATA_DT <= (SELECT MAX(DATA_DT) FROM base_indicator)
      AND PROP_STATUS_FLG = ''1''
      AND ECIF_CUST_ID IN (SELECT DISTINCT ECIF_CUST_ID FROM base_indicator WHERE ECIF_CUST_ID IS NOT NULL)
    GROUP BY ECIF_CUST_ID
),
valid_ratio AS (
    SELECT pb.ECIF_CUST_ID, pb.ACCOUNTING_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ECIF_CUST_ID = lt.ECIF_CUST_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCOUNTING_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ECIF_CUST_ID = vr.ECIF_CUST_ID
GROUP BY vr.ACCOUNTING_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;'
        WHEN 6 THEN 'WITH base_indicator AS (
    SELECT
        P1.ECIF_CUST_ID,
        P1.ACCNT_ORG_ID AS org_id,
        CASE
            WHEN P1.MNG_ACCNT_PROD_ID LIKE ''L11002%'' OR P1.MNG_ACCNT_PROD_ID LIKE ''L12002%'' THEN P1.CUR_BAL
            WHEN (P1.MNG_ACCNT_PROD_ID LIKE ''L11001%'' OR P1.MNG_ACCNT_PROD_ID LIKE ''L12001%'')
                 AND CAST(P1.ACCT_TERM AS DECIMAL(18, 4)) <= 730 THEN P1.CUR_BAL
            WHEN (P1.MNG_ACCNT_PROD_ID LIKE ''L11001%'' OR P1.MNG_ACCNT_PROD_ID LIKE ''L12001%'')
                 AND CAST(P1.ACCT_TERM AS DECIMAL(18, 4)) > 730
                 AND P1.EXEC_RATE <= P4.PARA_SCOPE THEN P1.CUR_BAL
            ELSE 0
        END AS metric_value_2,
        P1.DATA_DT
    FROM shenzhen_data.i01_sz_acct_sum_d_history P1
    LEFT JOIN shenzhen_data.FDL_REFL_DIM_PARAMET_CONFIG P4
        ON (CASE
                WHEN SUBSTR(P1.MNG_ACCNT_PROD_ID, 1, 6) = ''L12001'' THEN ''CORP_DEP_RT''
                WHEN SUBSTR(P1.MNG_ACCNT_PROD_ID, 1, 6) = ''L11001'' THEN ''INDIV_DEP_RT''
                ELSE ''''
            END) = P4.DIM_CD
       AND P1.INT_ST_DT >= CAST(P4.PARA_ST_VAL AS DATE)
       AND P1.INT_ST_DT < CAST(P4.PARA_END_VAL AS DATE)
       AND (CASE
                WHEN CAST(P1.ACCT_TERM AS DECIMAL(18, 4)) > 730 THEN ''3Y''
                ELSE ''''
            END) = P4.PARA_CD
       AND P4.YEAR = SUBSTR(''{data_dt}'', 1, 4)
       AND P4.BIZ_TYPE_CD = ''B_DP_RT''
    WHERE P1.DATA_DT = ''{data_dt}''
      AND P1.BASIS_CD IN (''D_100'')
      AND P1.CCY_CD IN (''156'', ''B02'')
      AND SUBSTR(P1.MNG_ACCNT_PROD_ID, 1, 4) = ''L110''
      AND (''{org_id}'' = '''' OR P1.ACCNT_ORG_ID = ''{org_id}'')
),
latest_time AS (
    SELECT ECIF_CUST_ID, MAX(DATA_DT) AS max_data_dt
    FROM shenzhen_data.shenzhen_prop_status
    WHERE DATA_DT <= (SELECT MAX(DATA_DT) FROM base_indicator)
      AND PROP_STATUS_FLG = ''1''
      AND ECIF_CUST_ID IN (SELECT DISTINCT ECIF_CUST_ID FROM base_indicator WHERE ECIF_CUST_ID IS NOT NULL)
    GROUP BY ECIF_CUST_ID
),
valid_ratio AS (
    SELECT pb.ECIF_CUST_ID, pb.ACCOUNTING_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ECIF_CUST_ID = lt.ECIF_CUST_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCOUNTING_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ECIF_CUST_ID = vr.ECIF_CUST_ID
GROUP BY vr.ACCOUNTING_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;'
        WHEN 7 THEN 'WITH base_indicator AS (
    SELECT
        ECIF_CUST_ID,
        ACCNT_ORG_ID AS org_id,
        NONSAVING_SCALE AS metric_value_2,
        DATA_DT
    FROM shenzhen_data.i01_sz_indiv_asset_data_tbl_history
    WHERE DATA_DT = ''{data_dt}''
      AND (''{org_id}'' = '''' OR ACCNT_ORG_ID = ''{org_id}'')
),
latest_time AS (
    SELECT
        ECIF_CUST_ID,
        MAX(DATA_DT) AS max_data_dt
    FROM shenzhen_data.shenzhen_prop_status
    WHERE DATA_DT <= (SELECT MAX(DATA_DT) FROM base_indicator)
      AND PROP_STATUS_FLG = ''1''
      AND ECIF_CUST_ID IN (
          SELECT DISTINCT ECIF_CUST_ID
          FROM base_indicator
          WHERE ECIF_CUST_ID IS NOT NULL
      )
    GROUP BY ECIF_CUST_ID
),
valid_ratio AS (
    SELECT
        pb.ECIF_CUST_ID,
        pb.ACCOUNTING_ORG_ID,
        pb.employee_no,
        pb.employee_name,
        pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ECIF_CUST_ID = lt.ECIF_CUST_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCOUNTING_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ECIF_CUST_ID = vr.ECIF_CUST_ID
GROUP BY vr.ACCOUNTING_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;'
        WHEN 9 THEN 'WITH base_indicator AS (
    SELECT
        ECIF_CUST_ID,
        ACCNT_ORG_ID AS org_id,
        CUR_BAL AS metric_value_2,
        DATA_DT
    FROM shenzhen_data.i01_sz_acct_sum_d_history
    WHERE DATA_DT = ''{data_dt}''
      AND SUBSTR(MNG_ACCNT_PROD_ID, 1, 4) = ''A110''
      AND MNG_ACCNT_PROD_ID <> ''A11001014001''
      AND (''{org_id}'' = '''' OR ACCNT_ORG_ID = ''{org_id}'')
),
latest_time AS (
    SELECT ECIF_CUST_ID, MAX(DATA_DT) AS max_data_dt
    FROM shenzhen_data.shenzhen_prop_status
    WHERE DATA_DT <= (SELECT MAX(DATA_DT) FROM base_indicator)
      AND PROP_STATUS_FLG = ''1''
      AND ECIF_CUST_ID IN (SELECT DISTINCT ECIF_CUST_ID FROM base_indicator WHERE ECIF_CUST_ID IS NOT NULL)
    GROUP BY ECIF_CUST_ID
),
valid_ratio AS (
    SELECT pb.ECIF_CUST_ID, pb.ACCOUNTING_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ECIF_CUST_ID = lt.ECIF_CUST_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCOUNTING_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ECIF_CUST_ID = vr.ECIF_CUST_ID
GROUP BY vr.ACCOUNTING_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;'
        WHEN 10 THEN 'WITH base_indicator AS (
    SELECT
        ECIF_CUST_ID,
        ACCNT_ORG_ID AS org_id,
        CUR_BAL AS metric_value_2,
        DATA_DT
    FROM shenzhen_data.i01_sz_acct_sum_d_history
    WHERE DATA_DT = ''{data_dt}''
      AND SUBSTR(MNG_ACCNT_PROD_ID, 1, 4) = ''A110''
      AND MNG_ACCNT_PROD_ID = ''A11001014001''
      AND (''{org_id}'' = '''' OR ACCNT_ORG_ID = ''{org_id}'')
),
latest_time AS (
    SELECT ECIF_CUST_ID, MAX(DATA_DT) AS max_data_dt
    FROM shenzhen_data.shenzhen_prop_status
    WHERE DATA_DT <= (SELECT MAX(DATA_DT) FROM base_indicator)
      AND PROP_STATUS_FLG = ''1''
      AND ECIF_CUST_ID IN (SELECT DISTINCT ECIF_CUST_ID FROM base_indicator WHERE ECIF_CUST_ID IS NOT NULL)
    GROUP BY ECIF_CUST_ID
),
valid_ratio AS (
    SELECT pb.ECIF_CUST_ID, pb.ACCOUNTING_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ECIF_CUST_ID = lt.ECIF_CUST_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCOUNTING_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ECIF_CUST_ID = vr.ECIF_CUST_ID
GROUP BY vr.ACCOUNTING_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;'
        WHEN 11 THEN 'WITH base_indicator AS (
    SELECT
        ECIF_CUST_ID,
        ACCNT_ORG_ID AS org_id,
        CUR_BAL AS metric_value_2,
        DATA_DT
    FROM shenzhen_data.i01_sz_acct_sum_d_history
    WHERE DATA_DT = ''{data_dt}''
      AND SUBSTR(MNG_ACCNT_PROD_ID, 1, 4) = ''A110''
      AND INCR_LOAN_FLG = ''1''
      AND CCY_CD IN (''156'', ''B02'')
      AND (''{org_id}'' = '''' OR ACCNT_ORG_ID = ''{org_id}'')
),
latest_time AS (
    SELECT ECIF_CUST_ID, MAX(DATA_DT) AS max_data_dt
    FROM shenzhen_data.shenzhen_prop_status
    WHERE DATA_DT <= (SELECT MAX(DATA_DT) FROM base_indicator)
      AND PROP_STATUS_FLG = ''1''
      AND ECIF_CUST_ID IN (SELECT DISTINCT ECIF_CUST_ID FROM base_indicator WHERE ECIF_CUST_ID IS NOT NULL)
    GROUP BY ECIF_CUST_ID
),
valid_ratio AS (
    SELECT pb.ECIF_CUST_ID, pb.ACCOUNTING_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ECIF_CUST_ID = lt.ECIF_CUST_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCOUNTING_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ECIF_CUST_ID = vr.ECIF_CUST_ID
GROUP BY vr.ACCOUNTING_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;'
        WHEN 12 THEN 'WITH base_indicator AS (
    SELECT
        ORIG_ACCT_ID,
        ACCNT_ORG_ID AS org_id,
        CUR_BAL + INT_ADJUST_AMT AS metric_value_2,
        DATA_DT
    FROM shenzhen_data.i01_sz_acct_sum_d_history
    WHERE DATA_DT = ''{data_dt}''
      AND LINE_ID <> ''L0103''
      AND CCY_CD IN (''156'', ''B02'')
      AND (MNG_ACCNT_PROD_ID LIKE ''A12001%'' OR MNG_ACCNT_PROD_ID LIKE ''A12002%'' OR MNG_ACCNT_PROD_ID LIKE ''A12003%'' OR MNG_ACCNT_PROD_ID LIKE ''A12005%'')
      AND MNG_ACCNT_PROD_ID NOT IN (''A12002015001'', ''A12004001005'', ''A12004002004'')
      AND (''{org_id}'' = '''' OR ACCNT_ORG_ID = ''{org_id}'')
),
latest_time AS (
    SELECT ORIG_ACCT_ID, MAX(DATA_DT) AS max_data_dt
    FROM shenzhen_data.shenzhen_prop_status
    WHERE DATA_DT <= (SELECT MAX(DATA_DT) FROM base_indicator)
      AND PROP_STATUS_FLG = ''1''
      AND ORIG_ACCT_ID IN (SELECT DISTINCT ORIG_ACCT_ID FROM base_indicator WHERE ORIG_ACCT_ID IS NOT NULL)
    GROUP BY ORIG_ACCT_ID
),
valid_ratio AS (
    SELECT pb.ORIG_ACCT_ID, pb.ACCOUNTING_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ORIG_ACCT_ID = lt.ORIG_ACCT_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCOUNTING_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ORIG_ACCT_ID = vr.ORIG_ACCT_ID
GROUP BY vr.ACCOUNTING_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;'
        WHEN 13 THEN 'WITH base_indicator AS (
    SELECT
        ORIG_ACCT_ID,
        ACCNT_ORG_ID AS org_id,
        CUR_BAL + INT_ADJUST_AMT AS metric_value_2,
        DATA_DT
    FROM shenzhen_data.i01_sz_acct_sum_d_history
    WHERE DATA_DT = ''{data_dt}''
      AND LINE_ID = ''L0103''
      AND CCY_CD IN (''156'', ''B02'')
      AND (MNG_ACCNT_PROD_ID LIKE ''A12001%'' OR MNG_ACCNT_PROD_ID LIKE ''A12002%'' OR MNG_ACCNT_PROD_ID LIKE ''A12003%'' OR MNG_ACCNT_PROD_ID LIKE ''A12005%'')
      AND MNG_ACCNT_PROD_ID NOT IN (''A12002015001'', ''A12004001005'', ''A12004002004'')
      AND (''{org_id}'' = '''' OR ACCNT_ORG_ID = ''{org_id}'')
),
latest_time AS (
    SELECT ORIG_ACCT_ID, MAX(DATA_DT) AS max_data_dt
    FROM shenzhen_data.shenzhen_prop_status
    WHERE DATA_DT <= (SELECT MAX(DATA_DT) FROM base_indicator)
      AND PROP_STATUS_FLG = ''1''
      AND ORIG_ACCT_ID IN (SELECT DISTINCT ORIG_ACCT_ID FROM base_indicator WHERE ORIG_ACCT_ID IS NOT NULL)
    GROUP BY ORIG_ACCT_ID
),
valid_ratio AS (
    SELECT pb.ORIG_ACCT_ID, pb.ACCOUNTING_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ORIG_ACCT_ID = lt.ORIG_ACCT_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCOUNTING_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ORIG_ACCT_ID = vr.ORIG_ACCT_ID
GROUP BY vr.ACCOUNTING_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;'
        WHEN 14 THEN 'WITH base_indicator AS (
    SELECT
        ORIG_ACCT_ID,
        ACCNT_ORG_ID AS org_id,
        CUR_BAL + INT_ADJUST_AMT AS metric_value_2,
        DATA_DT
    FROM shenzhen_data.i01_sz_acct_sum_d_history
    WHERE DATA_DT = ''{data_dt}''
      AND CCY_CD IN (''156'', ''B02'')
      AND ORIG_AMT <= 10000000
      AND SUBSTR(MNG_ACCNT_PROD_ID, 1, 4) = ''A120''
      AND (MNG_ACCNT_PROD_ID LIKE ''A12001%'' OR MNG_ACCNT_PROD_ID LIKE ''A12002%'')
      AND MNG_ACCNT_PROD_ID NOT IN (''A12002015001'', ''A12004001005'', ''A12004002004'')
      AND (''{org_id}'' = '''' OR ACCNT_ORG_ID = ''{org_id}'')
      AND ECIF_CUST_ID IN (
          SELECT ECIF_CUST_ID
          FROM shenzhen_data.i01_sz_corp_cust_basic_info_history
          WHERE DATA_DT = ''{data_dt}''
            AND INCLSV_SMALL_CUST_FLG = ''1''
      )
),
latest_time AS (
    SELECT ORIG_ACCT_ID, MAX(DATA_DT) AS max_data_dt
    FROM shenzhen_data.shenzhen_prop_status
    WHERE DATA_DT <= (SELECT MAX(DATA_DT) FROM base_indicator)
      AND PROP_STATUS_FLG = ''1''
      AND ORIG_ACCT_ID IN (SELECT DISTINCT ORIG_ACCT_ID FROM base_indicator WHERE ORIG_ACCT_ID IS NOT NULL)
    GROUP BY ORIG_ACCT_ID
),
valid_ratio AS (
    SELECT pb.ORIG_ACCT_ID, pb.ACCOUNTING_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ORIG_ACCT_ID = lt.ORIG_ACCT_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCOUNTING_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ORIG_ACCT_ID = vr.ORIG_ACCT_ID
GROUP BY vr.ACCOUNTING_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;'
        WHEN 15 THEN 'WITH base_indicator AS (
    SELECT
        ORIG_ACCT_ID,
        ACCNT_ORG_ID AS org_id,
        CUR_BAL + INT_ADJUST_AMT AS metric_value_2,
        DATA_DT
    FROM shenzhen_data.i01_sz_acct_sum_d_history
    WHERE DATA_DT = ''{data_dt}''
      AND MANUF_INDUS_LOAN_FLG = ''1''
      AND CCY_CD IN (''156'', ''B02'')
      AND (''{org_id}'' = '''' OR ACCNT_ORG_ID = ''{org_id}'')
),
latest_time AS (
    SELECT ORIG_ACCT_ID, MAX(DATA_DT) AS max_data_dt
    FROM shenzhen_data.shenzhen_prop_status
    WHERE DATA_DT <= (SELECT MAX(DATA_DT) FROM base_indicator)
      AND PROP_STATUS_FLG = ''1''
      AND ORIG_ACCT_ID IN (SELECT DISTINCT ORIG_ACCT_ID FROM base_indicator WHERE ORIG_ACCT_ID IS NOT NULL)
    GROUP BY ORIG_ACCT_ID
),
valid_ratio AS (
    SELECT pb.ORIG_ACCT_ID, pb.ACCOUNTING_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ORIG_ACCT_ID = lt.ORIG_ACCT_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCOUNTING_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ORIG_ACCT_ID = vr.ORIG_ACCT_ID
GROUP BY vr.ACCOUNTING_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;'
        WHEN 16 THEN 'WITH base_indicator AS (
    SELECT
        ORIG_ACCT_ID,
        ACCNT_ORG_ID AS org_id,
        CUR_BAL + INT_ADJUST_AMT AS metric_value_2,
        DATA_DT
    FROM shenzhen_data.i01_sz_acct_sum_d_history
    WHERE DATA_DT = ''{data_dt}''
      AND MANUF_INDUS_LONGTERM_LOAN_FLG = ''1''
      AND CCY_CD IN (''156'', ''B02'')
      AND (''{org_id}'' = '''' OR ACCNT_ORG_ID = ''{org_id}'')
),
latest_time AS (
    SELECT ORIG_ACCT_ID, MAX(DATA_DT) AS max_data_dt
    FROM shenzhen_data.shenzhen_prop_status
    WHERE DATA_DT <= (SELECT MAX(DATA_DT) FROM base_indicator)
      AND PROP_STATUS_FLG = ''1''
      AND ORIG_ACCT_ID IN (SELECT DISTINCT ORIG_ACCT_ID FROM base_indicator WHERE ORIG_ACCT_ID IS NOT NULL)
    GROUP BY ORIG_ACCT_ID
),
valid_ratio AS (
    SELECT pb.ORIG_ACCT_ID, pb.ACCOUNTING_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ORIG_ACCT_ID = lt.ORIG_ACCT_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCOUNTING_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ORIG_ACCT_ID = vr.ORIG_ACCT_ID
GROUP BY vr.ACCOUNTING_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;'
        WHEN 17 THEN 'WITH base_indicator AS (
    SELECT
        ORIG_ACCT_ID,
        ACCNT_ORG_ID AS org_id,
        CUR_BAL + INT_ADJUST_AMT AS metric_value_2,
        DATA_DT
    FROM shenzhen_data.i01_sz_acct_sum_d_history
    WHERE DATA_DT = ''{data_dt}''
      AND STRA_EMERGE_INDUS_FLG = ''1''
      AND CCY_CD IN (''156'', ''B02'')
      AND (''{org_id}'' = '''' OR ACCNT_ORG_ID = ''{org_id}'')
),
latest_time AS (
    SELECT ORIG_ACCT_ID, MAX(DATA_DT) AS max_data_dt
    FROM shenzhen_data.shenzhen_prop_status
    WHERE DATA_DT <= (SELECT MAX(DATA_DT) FROM base_indicator)
      AND PROP_STATUS_FLG = ''1''
      AND ORIG_ACCT_ID IN (SELECT DISTINCT ORIG_ACCT_ID FROM base_indicator WHERE ORIG_ACCT_ID IS NOT NULL)
    GROUP BY ORIG_ACCT_ID
),
valid_ratio AS (
    SELECT pb.ORIG_ACCT_ID, pb.ACCOUNTING_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ORIG_ACCT_ID = lt.ORIG_ACCT_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCOUNTING_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ORIG_ACCT_ID = vr.ORIG_ACCT_ID
GROUP BY vr.ACCOUNTING_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;'
        WHEN 18 THEN 'WITH base_indicator AS (
    SELECT
        ORIG_ACCT_ID,
        ACCNT_ORG_ID AS org_id,
        CUR_BAL + INT_ADJUST_AMT AS metric_value_2,
        DATA_DT
    FROM shenzhen_data.i01_sz_acct_sum_d_history
    WHERE DATA_DT = ''{data_dt}''
      AND TECH_INNO_LOAN_FLG = ''1''
      AND CCY_CD IN (''156'', ''B02'')
      AND (''{org_id}'' = '''' OR ACCNT_ORG_ID = ''{org_id}'')
),
latest_time AS (
    SELECT ORIG_ACCT_ID, MAX(DATA_DT) AS max_data_dt
    FROM shenzhen_data.shenzhen_prop_status
    WHERE DATA_DT <= (SELECT MAX(DATA_DT) FROM base_indicator)
      AND PROP_STATUS_FLG = ''1''
      AND ORIG_ACCT_ID IN (SELECT DISTINCT ORIG_ACCT_ID FROM base_indicator WHERE ORIG_ACCT_ID IS NOT NULL)
    GROUP BY ORIG_ACCT_ID
),
valid_ratio AS (
    SELECT pb.ORIG_ACCT_ID, pb.ACCOUNTING_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ORIG_ACCT_ID = lt.ORIG_ACCT_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCOUNTING_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ORIG_ACCT_ID = vr.ORIG_ACCT_ID
GROUP BY vr.ACCOUNTING_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;'
        WHEN 19 THEN 'WITH base_indicator AS (
    SELECT
        ORIG_ACCT_ID,
        ACCNT_ORG_ID AS org_id,
        CUR_BAL + INT_ADJUST_AMT AS metric_value_2,
        DATA_DT
    FROM shenzhen_data.i01_sz_acct_sum_d_history
    WHERE DATA_DT = ''{data_dt}''
      AND GREEN_LOAN_FLG = ''1''
      AND CCY_CD IN (''156'', ''B02'')
      AND (''{org_id}'' = '''' OR ACCNT_ORG_ID = ''{org_id}'')
),
latest_time AS (
    SELECT ORIG_ACCT_ID, MAX(DATA_DT) AS max_data_dt
    FROM shenzhen_data.shenzhen_prop_status
    WHERE DATA_DT <= (SELECT MAX(DATA_DT) FROM base_indicator)
      AND PROP_STATUS_FLG = ''1''
      AND ORIG_ACCT_ID IN (SELECT DISTINCT ORIG_ACCT_ID FROM base_indicator WHERE ORIG_ACCT_ID IS NOT NULL)
    GROUP BY ORIG_ACCT_ID
),
valid_ratio AS (
    SELECT pb.ORIG_ACCT_ID, pb.ACCOUNTING_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ORIG_ACCT_ID = lt.ORIG_ACCT_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCOUNTING_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ORIG_ACCT_ID = vr.ORIG_ACCT_ID
GROUP BY vr.ACCOUNTING_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;'
        WHEN 21 THEN 'WITH base_indicator AS (
    SELECT
        ECIF_CUST_ID,
        ACCNT_ORG_ID AS org_id,
        BAD_LOAN_AMT AS metric_value_2,
        DATA_DT
    FROM shenzhen_data.i01_sz_acct_sum_d_history
    WHERE DATA_DT = ''{data_dt}''
      AND SUBSTR(MNG_ACCNT_PROD_ID, 1, 4) = ''A110''
      AND MNG_ACCNT_PROD_ID <> ''A11001014001''
      AND (''{org_id}'' = '''' OR ACCNT_ORG_ID = ''{org_id}'')
),
latest_time AS (
    SELECT ECIF_CUST_ID, MAX(DATA_DT) AS max_data_dt
    FROM shenzhen_data.shenzhen_prop_status
    WHERE DATA_DT <= (SELECT MAX(DATA_DT) FROM base_indicator)
      AND PROP_STATUS_FLG = ''1''
      AND ECIF_CUST_ID IN (SELECT DISTINCT ECIF_CUST_ID FROM base_indicator WHERE ECIF_CUST_ID IS NOT NULL)
    GROUP BY ECIF_CUST_ID
),
valid_ratio AS (
    SELECT pb.ECIF_CUST_ID, pb.ACCOUNTING_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ECIF_CUST_ID = lt.ECIF_CUST_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCOUNTING_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ECIF_CUST_ID = vr.ECIF_CUST_ID
GROUP BY vr.ACCOUNTING_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;'
        WHEN 22 THEN 'WITH base_indicator AS (
    SELECT
        ORIG_ACCT_ID,
        ACCNT_ORG_ID AS org_id,
        BAD_LOAN_AMT AS metric_value_2,
        DATA_DT
    FROM shenzhen_data.i01_sz_acct_sum_d_history
    WHERE DATA_DT = ''{data_dt}''
      AND LINE_ID <> ''L0103''
      AND CCY_CD IN (''156'', ''B02'')
      AND (MNG_ACCNT_PROD_ID LIKE ''A12001%'' OR MNG_ACCNT_PROD_ID LIKE ''A12002%'' OR MNG_ACCNT_PROD_ID LIKE ''A12003%'' OR MNG_ACCNT_PROD_ID LIKE ''A12005%'')
      AND MNG_ACCNT_PROD_ID NOT IN (''A12002015001'', ''A12004001005'', ''A12004002004'')
      AND (''{org_id}'' = '''' OR ACCNT_ORG_ID = ''{org_id}'')
),
latest_time AS (
    SELECT ORIG_ACCT_ID, MAX(DATA_DT) AS max_data_dt
    FROM shenzhen_data.shenzhen_prop_status
    WHERE DATA_DT <= (SELECT MAX(DATA_DT) FROM base_indicator)
      AND PROP_STATUS_FLG = ''1''
      AND ORIG_ACCT_ID IN (SELECT DISTINCT ORIG_ACCT_ID FROM base_indicator WHERE ORIG_ACCT_ID IS NOT NULL)
    GROUP BY ORIG_ACCT_ID
),
valid_ratio AS (
    SELECT pb.ORIG_ACCT_ID, pb.ACCOUNTING_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ORIG_ACCT_ID = lt.ORIG_ACCT_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCOUNTING_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ORIG_ACCT_ID = vr.ORIG_ACCT_ID
GROUP BY vr.ACCOUNTING_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;'
        WHEN 23 THEN 'WITH base_indicator AS (
    SELECT
        ORIG_ACCT_ID,
        ACCNT_ORG_ID AS org_id,
        BAD_LOAN_AMT AS metric_value_2,
        DATA_DT
    FROM shenzhen_data.i01_sz_acct_sum_d_history
    WHERE DATA_DT = ''{data_dt}''
      AND LINE_ID = ''L0103''
      AND CCY_CD IN (''156'', ''B02'')
      AND (MNG_ACCNT_PROD_ID LIKE ''A12001%'' OR MNG_ACCNT_PROD_ID LIKE ''A12002%'' OR MNG_ACCNT_PROD_ID LIKE ''A12003%'' OR MNG_ACCNT_PROD_ID LIKE ''A12005%'')
      AND MNG_ACCNT_PROD_ID NOT IN (''A12002015001'', ''A12004001005'', ''A12004002004'')
      AND (''{org_id}'' = '''' OR ACCNT_ORG_ID = ''{org_id}'')
),
latest_time AS (
    SELECT ORIG_ACCT_ID, MAX(DATA_DT) AS max_data_dt
    FROM shenzhen_data.shenzhen_prop_status
    WHERE DATA_DT <= (SELECT MAX(DATA_DT) FROM base_indicator)
      AND PROP_STATUS_FLG = ''1''
      AND ORIG_ACCT_ID IN (SELECT DISTINCT ORIG_ACCT_ID FROM base_indicator WHERE ORIG_ACCT_ID IS NOT NULL)
    GROUP BY ORIG_ACCT_ID
),
valid_ratio AS (
    SELECT pb.ORIG_ACCT_ID, pb.ACCOUNTING_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ORIG_ACCT_ID = lt.ORIG_ACCT_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCOUNTING_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ORIG_ACCT_ID = vr.ORIG_ACCT_ID
GROUP BY vr.ACCOUNTING_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;'
        WHEN 24 THEN 'WITH base_indicator AS (
    SELECT
        ECIF_CUST_ID,
        ACCNT_ORG_ID AS org_id,
        CUR_BAL AS metric_value_2,
        DATA_DT
    FROM shenzhen_data.i01_sz_acct_sum_d_history
    WHERE DATA_DT = ''{data_dt}''
      AND SUBSTR(MNG_ACCNT_PROD_ID, 1, 4) = ''A110''
      AND MNG_ACCNT_PROD_ID <> ''A11001014001''
      AND OVERDUE_FLG = ''1''
      AND (''{org_id}'' = '''' OR ACCNT_ORG_ID = ''{org_id}'')
),
latest_time AS (
    SELECT ECIF_CUST_ID, MAX(DATA_DT) AS max_data_dt
    FROM shenzhen_data.shenzhen_prop_status
    WHERE DATA_DT <= (SELECT MAX(DATA_DT) FROM base_indicator)
      AND PROP_STATUS_FLG = ''1''
      AND ECIF_CUST_ID IN (SELECT DISTINCT ECIF_CUST_ID FROM base_indicator WHERE ECIF_CUST_ID IS NOT NULL)
    GROUP BY ECIF_CUST_ID
),
valid_ratio AS (
    SELECT pb.ECIF_CUST_ID, pb.ACCOUNTING_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ECIF_CUST_ID = lt.ECIF_CUST_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCOUNTING_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ECIF_CUST_ID = vr.ECIF_CUST_ID
GROUP BY vr.ACCOUNTING_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;'
        WHEN 25 THEN 'WITH base_indicator AS (
    SELECT
        ORIG_ACCT_ID,
        ACCNT_ORG_ID AS org_id,
        CUR_BAL + INT_ADJUST_AMT AS metric_value_2,
        DATA_DT
    FROM shenzhen_data.i01_sz_acct_sum_d_history
    WHERE DATA_DT = ''{data_dt}''
      AND LINE_ID <> ''L0103''
      AND CCY_CD IN (''156'', ''B02'')
      AND (MNG_ACCNT_PROD_ID LIKE ''A12001%'' OR MNG_ACCNT_PROD_ID LIKE ''A12002%'' OR MNG_ACCNT_PROD_ID LIKE ''A12003%'' OR MNG_ACCNT_PROD_ID LIKE ''A12005%'')
      AND MNG_ACCNT_PROD_ID NOT IN (''A12002015001'', ''A12004001005'', ''A12004002004'')
      AND OVERDUE_FLG = ''1''
      AND (''{org_id}'' = '''' OR ACCNT_ORG_ID = ''{org_id}'')
),
latest_time AS (
    SELECT ORIG_ACCT_ID, MAX(DATA_DT) AS max_data_dt
    FROM shenzhen_data.shenzhen_prop_status
    WHERE DATA_DT <= (SELECT MAX(DATA_DT) FROM base_indicator)
      AND PROP_STATUS_FLG = ''1''
      AND ORIG_ACCT_ID IN (SELECT DISTINCT ORIG_ACCT_ID FROM base_indicator WHERE ORIG_ACCT_ID IS NOT NULL)
    GROUP BY ORIG_ACCT_ID
),
valid_ratio AS (
    SELECT pb.ORIG_ACCT_ID, pb.ACCOUNTING_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ORIG_ACCT_ID = lt.ORIG_ACCT_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCOUNTING_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ORIG_ACCT_ID = vr.ORIG_ACCT_ID
GROUP BY vr.ACCOUNTING_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;'
        WHEN 26 THEN 'WITH base_indicator AS (
    SELECT
        ORIG_ACCT_ID,
        ACCNT_ORG_ID AS org_id,
        CUR_BAL + INT_ADJUST_AMT AS metric_value_2,
        DATA_DT
    FROM shenzhen_data.i01_sz_acct_sum_d_history
    WHERE DATA_DT = ''{data_dt}''
      AND LINE_ID = ''L0103''
      AND CCY_CD IN (''156'', ''B02'')
      AND (MNG_ACCNT_PROD_ID LIKE ''A12001%'' OR MNG_ACCNT_PROD_ID LIKE ''A12002%'' OR MNG_ACCNT_PROD_ID LIKE ''A12003%'' OR MNG_ACCNT_PROD_ID LIKE ''A12005%'')
      AND MNG_ACCNT_PROD_ID NOT IN (''A12002015001'', ''A12004001005'', ''A12004002004'')
      AND OVERDUE_FLG = ''1''
      AND (''{org_id}'' = '''' OR ACCNT_ORG_ID = ''{org_id}'')
),
latest_time AS (
    SELECT ORIG_ACCT_ID, MAX(DATA_DT) AS max_data_dt
    FROM shenzhen_data.shenzhen_prop_status
    WHERE DATA_DT <= (SELECT MAX(DATA_DT) FROM base_indicator)
      AND PROP_STATUS_FLG = ''1''
      AND ORIG_ACCT_ID IN (SELECT DISTINCT ORIG_ACCT_ID FROM base_indicator WHERE ORIG_ACCT_ID IS NOT NULL)
    GROUP BY ORIG_ACCT_ID
),
valid_ratio AS (
    SELECT pb.ORIG_ACCT_ID, pb.ACCOUNTING_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ORIG_ACCT_ID = lt.ORIG_ACCT_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCOUNTING_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ORIG_ACCT_ID = vr.ORIG_ACCT_ID
GROUP BY vr.ACCOUNTING_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;'
    END AS point_sql_template,
    CASE r.indicator_id
        WHEN 2 THEN 'WITH params AS (
    SELECT
        DATE(CONCAT(SUBSTR(''{data_dt}'', 1, 4), ''-01-01'')) AS period_start,
        DATE(CONCAT(SUBSTR(''{data_dt}'', 1, 4), ''-12-31'')) AS period_end
),
acct_daily_accum AS (
    SELECT
        a.ORIG_ACCT_ID,
        a.DATA_DT,
        a.BAL_YEAR_ACCUM AS accum_balance
    FROM shenzhen_data.i01_sz_acct_sum_d_history a
    CROSS JOIN params pm
    WHERE a.DATA_DT BETWEEN pm.period_start AND pm.period_end
      AND SUBSTR(a.MNG_ACCNT_PROD_ID, 1, 4) = ''L120''
      AND a.CCY_CD IN (''156'', ''B02'')
      AND (''{org_id}'' = '''' OR RIGHT(a.MNG_ORG_ID, 8) = ''{org_id}'')
),
prop_raw AS (
    SELECT
        p.ORIG_ACCT_ID,
        p.DATA_DT AS eff_date,
        p.ACCOUNTING_ORG_ID AS org_id,
        p.employee_no,
        p.employee_name,
        p.KPI_PROP,
        p.YEAR_BASE_AMOUNT
    FROM shenzhen_data.shenzhen_prop_status p
    CROSS JOIN params pm
    WHERE p.DATA_DT <= pm.period_end
      AND p.PROP_STATUS_FLG = ''1''
),
distinct_eff_dates AS (
    SELECT DISTINCT
        pr.ORIG_ACCT_ID,
        pr.eff_date
    FROM prop_raw pr
    CROSS JOIN params pm
    WHERE pr.eff_date >= pm.period_start
),
all_starts AS (
    SELECT ORIG_ACCT_ID, eff_date AS start_date FROM distinct_eff_dates
    UNION ALL
    SELECT a.ORIG_ACCT_ID, pm.period_start AS start_date
    FROM (SELECT DISTINCT ORIG_ACCT_ID FROM acct_daily_accum WHERE ORIG_ACCT_ID IS NOT NULL) a
    CROSS JOIN params pm
    LEFT JOIN distinct_eff_dates d ON a.ORIG_ACCT_ID = d.ORIG_ACCT_ID
    WHERE d.ORIG_ACCT_ID IS NULL
    UNION ALL
    SELECT a.ORIG_ACCT_ID, pm.period_start AS start_date
    FROM (SELECT DISTINCT ORIG_ACCT_ID FROM acct_daily_accum WHERE ORIG_ACCT_ID IS NOT NULL) a
    CROSS JOIN params pm
    INNER JOIN distinct_eff_dates d ON a.ORIG_ACCT_ID = d.ORIG_ACCT_ID
    GROUP BY a.ORIG_ACCT_ID, pm.period_start
    HAVING MIN(d.eff_date) > pm.period_start
),
intervals AS (
    SELECT
        ORIG_ACCT_ID,
        start_date AS interval_start,
        LEAD(start_date, 1, DATE_ADD(pm.period_end, INTERVAL 1 DAY))
            OVER (PARTITION BY ORIG_ACCT_ID ORDER BY start_date) AS interval_end
    FROM all_starts
    CROSS JOIN params pm
),
latest_prop_before_start AS (
    SELECT
        i.ORIG_ACCT_ID,
        i.interval_start,
        p.org_id,
        p.employee_no,
        p.employee_name,
        p.KPI_PROP,
        p.YEAR_BASE_AMOUNT,
        ROW_NUMBER() OVER (
            PARTITION BY i.ORIG_ACCT_ID, i.interval_start
            ORDER BY p.eff_date DESC
        ) AS rn
    FROM intervals i
    INNER JOIN prop_raw p
        ON i.ORIG_ACCT_ID = p.ORIG_ACCT_ID
       AND p.eff_date <= i.interval_start
),
interval_props AS (
    SELECT
        i.ORIG_ACCT_ID,
        i.interval_start,
        i.interval_end,
        lp.org_id,
        lp.employee_no,
        lp.employee_name,
        lp.KPI_PROP,
        CASE WHEN i.interval_start = pm.period_start THEN 0 ELSE lp.YEAR_BASE_AMOUNT END AS base_accum
    FROM intervals i
    CROSS JOIN params pm
    LEFT JOIN latest_prop_before_start lp
        ON i.ORIG_ACCT_ID = lp.ORIG_ACCT_ID
       AND i.interval_start = lp.interval_start
       AND lp.rn = 1
    WHERE i.interval_start < i.interval_end
),
org_ownership_span AS (
    SELECT
        ip.ORIG_ACCT_ID,
        ip.org_id,
        ip.employee_no,
        ip.employee_name,
        ip.interval_start AS eff_date,
        LEAD(ip.interval_start, 1, DATE_ADD(pm.period_end, INTERVAL 1 DAY))
            OVER (PARTITION BY ip.ORIG_ACCT_ID, ip.org_id, ip.employee_no ORDER BY ip.interval_start) AS exit_date,
        ip.KPI_PROP,
        ip.base_accum
    FROM interval_props ip
    CROSS JOIN params pm
    WHERE ip.org_id IS NOT NULL
),
daily_accum_by_org AS (
    SELECT
        a.ORIG_ACCT_ID,
        a.DATA_DT,
        o.org_id,
        o.employee_no,
        o.employee_name,
        a.accum_balance * o.KPI_PROP AS org_accum_share,
        o.eff_date,
        o.exit_date
    FROM acct_daily_accum a
    INNER JOIN org_ownership_span o
        ON a.ORIG_ACCT_ID = o.ORIG_ACCT_ID
       AND a.DATA_DT >= o.eff_date
       AND a.DATA_DT < o.exit_date
),
org_base AS (
    SELECT
        ORIG_ACCT_ID,
        org_id,
        employee_no,
        employee_name,
        SUM(base_accum * KPI_PROP) AS base_accum
    FROM org_ownership_span
    GROUP BY ORIG_ACCT_ID, org_id, employee_no, employee_name
),
org_active_accum AS (
    SELECT
        d.ORIG_ACCT_ID,
        d.DATA_DT,
        d.org_id,
        d.employee_no,
        d.employee_name,
        GREATEST(d.org_accum_share - b.base_accum, 0) AS effective_accum,
        d.exit_date
    FROM daily_accum_by_org d
    INNER JOIN org_base b
        ON d.ORIG_ACCT_ID = b.ORIG_ACCT_ID
       AND d.org_id = b.org_id
       AND d.employee_no = b.employee_no
),
org_exit_snapshot AS (
    SELECT DISTINCT
        ORIG_ACCT_ID,
        org_id,
        employee_no,
        employee_name,
        FIRST_VALUE(effective_accum) OVER (
            PARTITION BY ORIG_ACCT_ID, org_id, employee_no
            ORDER BY DATA_DT DESC
        ) AS frozen_accum
    FROM org_active_accum
),
org_min_eff_date AS (
    SELECT
        ORIG_ACCT_ID,
        org_id,
        employee_no,
        employee_name,
        MIN(eff_date) AS min_eff_date
    FROM org_ownership_span
    GROUP BY ORIG_ACCT_ID, org_id, employee_no, employee_name
),
all_dates AS (
    SELECT DISTINCT DATA_DT FROM acct_daily_accum
),
org_full_dates AS (
    SELECT
        s.ORIG_ACCT_ID,
        s.org_id,
        s.employee_no,
        s.employee_name,
        d.DATA_DT
    FROM org_exit_snapshot s
    INNER JOIN org_min_eff_date m
        ON s.ORIG_ACCT_ID = m.ORIG_ACCT_ID
       AND s.org_id = m.org_id
       AND s.employee_no = m.employee_no
    INNER JOIN all_dates d
        ON d.DATA_DT >= m.min_eff_date
    CROSS JOIN params pm
    WHERE d.DATA_DT <= pm.period_end
),
org_daily_accum_final AS (
    SELECT
        f.ORIG_ACCT_ID,
        f.DATA_DT,
        f.org_id,
        f.employee_no,
        f.employee_name,
        COALESCE(a.effective_accum, s.frozen_accum) AS effective_accum
    FROM org_full_dates f
    LEFT JOIN org_active_accum a
        ON f.ORIG_ACCT_ID = a.ORIG_ACCT_ID
       AND f.org_id = a.org_id
       AND f.employee_no = a.employee_no
       AND f.DATA_DT = a.DATA_DT
    LEFT JOIN org_exit_snapshot s
        ON f.ORIG_ACCT_ID = s.ORIG_ACCT_ID
       AND f.org_id = s.org_id
       AND f.employee_no = s.employee_no
),
daily_factor AS (
    SELECT
        DATA_DT,
        DATEDIFF(DATA_DT, DATE(CONCAT(YEAR(DATA_DT), ''-01-01''))) + 1 AS day_num
    FROM all_dates
),
org_daily_contrib AS (
    SELECT
        e.org_id,
        e.employee_no,
        e.employee_name,
        e.DATA_DT,
        e.effective_accum / f.day_num AS daily_contrib
    FROM org_daily_accum_final e
    INNER JOIN daily_factor f ON e.DATA_DT = f.DATA_DT
)
SELECT
    org_id,
    employee_no,
    employee_name,
    SUM(daily_contrib) AS metric_value
FROM org_daily_contrib
GROUP BY org_id, employee_no, employee_name
ORDER BY org_id, employee_no;'
        WHEN 3 THEN 'WITH params AS (
    SELECT
        DATE(CONCAT(SUBSTR(''{data_dt}'', 1, 4), ''-01-01'')) AS period_start,
        DATE(CONCAT(SUBSTR(''{data_dt}'', 1, 4), ''-12-31'')) AS period_end
),
acct_daily_accum AS (
    SELECT
        p1.ORIG_ACCT_ID,
        p1.DATA_DT,
        CASE
            WHEN p1.MNG_ACCNT_PROD_ID LIKE ''L11002%'' OR p1.MNG_ACCNT_PROD_ID LIKE ''L12002%'' THEN p1.BAL_YEAR_ACCUM
            WHEN (p1.MNG_ACCNT_PROD_ID LIKE ''L11001%'' OR p1.MNG_ACCNT_PROD_ID LIKE ''L12001%'')
                 AND CAST(p1.ACCT_TERM AS DECIMAL(18, 4)) <= 730 THEN p1.BAL_YEAR_ACCUM
            WHEN (p1.MNG_ACCNT_PROD_ID LIKE ''L11001%'' OR p1.MNG_ACCNT_PROD_ID LIKE ''L12001%'')
                 AND CAST(p1.ACCT_TERM AS DECIMAL(18, 4)) > 730
                 AND p1.EXEC_RATE <= p4.PARA_SCOPE THEN p1.BAL_YEAR_ACCUM
            ELSE 0
        END AS accum_balance
    FROM shenzhen_data.i01_sz_acct_sum_d_history p1
    LEFT JOIN shenzhen_data.FDL_REFL_DIM_PARAMET_CONFIG p4
        ON (CASE
                WHEN SUBSTR(p1.MNG_ACCNT_PROD_ID, 1, 6) = ''L12001'' THEN ''CORP_DEP_RT''
                WHEN SUBSTR(p1.MNG_ACCNT_PROD_ID, 1, 6) = ''L11001'' THEN ''INDIV_DEP_RT''
                ELSE ''''
            END) = p4.DIM_CD
       AND p1.INT_ST_DT >= CAST(p4.PARA_ST_VAL AS DATE)
       AND p1.INT_ST_DT < CAST(p4.PARA_END_VAL AS DATE)
       AND (CASE WHEN CAST(p1.ACCT_TERM AS DECIMAL(18, 4)) > 730 THEN ''3Y'' ELSE '''' END) = p4.PARA_CD
       AND p4.YEAR = SUBSTR(''{data_dt}'', 1, 4)
       AND p4.BIZ_TYPE_CD = ''B_DP_RT''
    CROSS JOIN params pm
    WHERE p1.DATA_DT BETWEEN pm.period_start AND pm.period_end
      AND p1.BASIS_CD IN (''D_100'')
      AND p1.CCY_CD IN (''156'', ''B02'')
      AND SUBSTR(p1.MNG_ACCNT_PROD_ID, 1, 4) = ''L120''
      AND (''{org_id}'' = '''' OR p1.ACCNT_ORG_ID = ''{org_id}'')
),
prop_raw AS (
    SELECT
        p.ORIG_ACCT_ID,
        p.DATA_DT AS eff_date,
        p.ACCOUNTING_ORG_ID AS org_id,
        p.employee_no,
        p.employee_name,
        p.KPI_PROP,
        p.YEAR_BASE_AMOUNT
    FROM shenzhen_data.shenzhen_prop_status p
    CROSS JOIN params pm
    WHERE p.DATA_DT <= pm.period_end
      AND p.PROP_STATUS_FLG = ''1''
),
distinct_eff_dates AS (
    SELECT DISTINCT ORIG_ACCT_ID, eff_date
    FROM prop_raw
    CROSS JOIN params pm
    WHERE eff_date >= pm.period_start
),
all_starts AS (
    SELECT ORIG_ACCT_ID, eff_date AS start_date FROM distinct_eff_dates
    UNION ALL
    SELECT a.ORIG_ACCT_ID, pm.period_start AS start_date
    FROM (SELECT DISTINCT ORIG_ACCT_ID FROM acct_daily_accum WHERE ORIG_ACCT_ID IS NOT NULL) a
    CROSS JOIN params pm
    LEFT JOIN distinct_eff_dates d ON a.ORIG_ACCT_ID = d.ORIG_ACCT_ID
    WHERE d.ORIG_ACCT_ID IS NULL
    UNION ALL
    SELECT a.ORIG_ACCT_ID, pm.period_start AS start_date
    FROM (SELECT DISTINCT ORIG_ACCT_ID FROM acct_daily_accum WHERE ORIG_ACCT_ID IS NOT NULL) a
    CROSS JOIN params pm
    INNER JOIN distinct_eff_dates d ON a.ORIG_ACCT_ID = d.ORIG_ACCT_ID
    GROUP BY a.ORIG_ACCT_ID, pm.period_start
    HAVING MIN(d.eff_date) > pm.period_start
),
intervals AS (
    SELECT
        ORIG_ACCT_ID,
        start_date AS interval_start,
        LEAD(start_date, 1, DATE_ADD(pm.period_end, INTERVAL 1 DAY))
            OVER (PARTITION BY ORIG_ACCT_ID ORDER BY start_date) AS interval_end
    FROM all_starts
    CROSS JOIN params pm
),
latest_prop_before_start AS (
    SELECT
        i.ORIG_ACCT_ID,
        i.interval_start,
        p.org_id,
        p.employee_no,
        p.employee_name,
        p.KPI_PROP,
        p.YEAR_BASE_AMOUNT,
        ROW_NUMBER() OVER (
            PARTITION BY i.ORIG_ACCT_ID, i.interval_start
            ORDER BY p.eff_date DESC
        ) AS rn
    FROM intervals i
    INNER JOIN prop_raw p
        ON i.ORIG_ACCT_ID = p.ORIG_ACCT_ID
       AND p.eff_date <= i.interval_start
),
interval_props AS (
    SELECT
        i.ORIG_ACCT_ID,
        i.interval_start,
        i.interval_end,
        lp.org_id,
        lp.employee_no,
        lp.employee_name,
        lp.KPI_PROP,
        CASE WHEN i.interval_start = pm.period_start THEN 0 ELSE lp.YEAR_BASE_AMOUNT END AS base_accum
    FROM intervals i
    CROSS JOIN params pm
    LEFT JOIN latest_prop_before_start lp
        ON i.ORIG_ACCT_ID = lp.ORIG_ACCT_ID
       AND i.interval_start = lp.interval_start
       AND lp.rn = 1
    WHERE i.interval_start < i.interval_end
),
org_ownership_span AS (
    SELECT
        ip.ORIG_ACCT_ID,
        ip.org_id,
        ip.employee_no,
        ip.employee_name,
        ip.interval_start AS eff_date,
        LEAD(ip.interval_start, 1, DATE_ADD(pm.period_end, INTERVAL 1 DAY))
            OVER (PARTITION BY ip.ORIG_ACCT_ID, ip.org_id, ip.employee_no ORDER BY ip.interval_start) AS exit_date,
        ip.KPI_PROP,
        ip.base_accum
    FROM interval_props ip
    CROSS JOIN params pm
    WHERE ip.org_id IS NOT NULL
),
daily_accum_by_org AS (
    SELECT
        a.ORIG_ACCT_ID,
        a.DATA_DT,
        o.org_id,
        o.employee_no,
        o.employee_name,
        a.accum_balance * o.KPI_PROP AS org_accum_share,
        o.eff_date,
        o.exit_date
    FROM acct_daily_accum a
    INNER JOIN org_ownership_span o
        ON a.ORIG_ACCT_ID = o.ORIG_ACCT_ID
       AND a.DATA_DT >= o.eff_date
       AND a.DATA_DT < o.exit_date
),
org_base AS (
    SELECT
        ORIG_ACCT_ID,
        org_id,
        employee_no,
        employee_name,
        SUM(base_accum * KPI_PROP) AS base_accum
    FROM org_ownership_span
    GROUP BY ORIG_ACCT_ID, org_id, employee_no, employee_name
),
org_active_accum AS (
    SELECT
        d.ORIG_ACCT_ID,
        d.DATA_DT,
        d.org_id,
        d.employee_no,
        d.employee_name,
        GREATEST(d.org_accum_share - b.base_accum, 0) AS effective_accum
    FROM daily_accum_by_org d
    INNER JOIN org_base b
        ON d.ORIG_ACCT_ID = b.ORIG_ACCT_ID
       AND d.org_id = b.org_id
       AND d.employee_no = b.employee_no
),
daily_factor AS (
    SELECT
        DATA_DT,
        DATEDIFF(DATA_DT, DATE(CONCAT(YEAR(DATA_DT), ''-01-01''))) + 1 AS day_num
    FROM (SELECT DISTINCT DATA_DT FROM acct_daily_accum) t
),
org_daily_contrib AS (
    SELECT
        a.org_id,
        a.employee_no,
        a.employee_name,
        a.DATA_DT,
        a.effective_accum / f.day_num AS daily_contrib
    FROM org_active_accum a
    INNER JOIN daily_factor f ON a.DATA_DT = f.DATA_DT
)
SELECT
    org_id,
    employee_no,
    employee_name,
    SUM(daily_contrib) AS metric_value
FROM org_daily_contrib
GROUP BY org_id, employee_no, employee_name
ORDER BY org_id, employee_no;'
        WHEN 4 THEN 'WITH params AS (
    SELECT
        DATE(CONCAT(SUBSTR(''{data_dt}'', 1, 4), ''-01-01'')) AS period_start,
        DATE(CONCAT(SUBSTR(''{data_dt}'', 1, 4), ''-12-31'')) AS period_end
),
acct_daily_accum AS (
    SELECT
        a.ORIG_ACCT_ID,
        a.DATA_DT,
        a.BAL_YEAR_ACCUM AS accum_balance
    FROM shenzhen_data.i01_sz_acct_sum_d_history a
    CROSS JOIN params pm
    WHERE a.DATA_DT BETWEEN pm.period_start AND pm.period_end
      AND SUBSTR(a.MNG_ACCNT_PROD_ID, 1, 4) = ''L120''
      AND a.CCY_CD IN (''156'', ''B02'')
      AND a.FIX_CUR_FLG = ''0''
      AND (''{org_id}'' = '''' OR RIGHT(a.MNG_ORG_ID, 8) = ''{org_id}'')
),
prop_raw AS (
    SELECT
        p.ORIG_ACCT_ID,
        p.DATA_DT AS eff_date,
        p.ACCOUNTING_ORG_ID AS org_id,
        p.employee_no,
        p.employee_name,
        p.KPI_PROP,
        p.YEAR_BASE_AMOUNT
    FROM shenzhen_data.shenzhen_prop_status p
    CROSS JOIN params pm
    WHERE p.DATA_DT <= pm.period_end
      AND p.PROP_STATUS_FLG = ''1''
),
distinct_eff_dates AS (
    SELECT DISTINCT ORIG_ACCT_ID, eff_date
    FROM prop_raw
    CROSS JOIN params pm
    WHERE eff_date >= pm.period_start
),
all_starts AS (
    SELECT ORIG_ACCT_ID, eff_date AS start_date FROM distinct_eff_dates
    UNION ALL
    SELECT a.ORIG_ACCT_ID, pm.period_start AS start_date
    FROM (SELECT DISTINCT ORIG_ACCT_ID FROM acct_daily_accum WHERE ORIG_ACCT_ID IS NOT NULL) a
    CROSS JOIN params pm
    LEFT JOIN distinct_eff_dates d ON a.ORIG_ACCT_ID = d.ORIG_ACCT_ID
    WHERE d.ORIG_ACCT_ID IS NULL
    UNION ALL
    SELECT a.ORIG_ACCT_ID, pm.period_start AS start_date
    FROM (SELECT DISTINCT ORIG_ACCT_ID FROM acct_daily_accum WHERE ORIG_ACCT_ID IS NOT NULL) a
    CROSS JOIN params pm
    INNER JOIN distinct_eff_dates d ON a.ORIG_ACCT_ID = d.ORIG_ACCT_ID
    GROUP BY a.ORIG_ACCT_ID, pm.period_start
    HAVING MIN(d.eff_date) > pm.period_start
),
intervals AS (
    SELECT
        ORIG_ACCT_ID,
        start_date AS interval_start,
        LEAD(start_date, 1, DATE_ADD(pm.period_end, INTERVAL 1 DAY))
            OVER (PARTITION BY ORIG_ACCT_ID ORDER BY start_date) AS interval_end
    FROM all_starts
    CROSS JOIN params pm
),
latest_prop_before_start AS (
    SELECT
        i.ORIG_ACCT_ID,
        i.interval_start,
        p.org_id,
        p.employee_no,
        p.employee_name,
        p.KPI_PROP,
        p.YEAR_BASE_AMOUNT,
        ROW_NUMBER() OVER (
            PARTITION BY i.ORIG_ACCT_ID, i.interval_start
            ORDER BY p.eff_date DESC
        ) AS rn
    FROM intervals i
    INNER JOIN prop_raw p
        ON i.ORIG_ACCT_ID = p.ORIG_ACCT_ID
       AND p.eff_date <= i.interval_start
),
interval_props AS (
    SELECT
        i.ORIG_ACCT_ID,
        i.interval_start,
        i.interval_end,
        lp.org_id,
        lp.employee_no,
        lp.employee_name,
        lp.KPI_PROP,
        CASE WHEN i.interval_start = pm.period_start THEN 0 ELSE lp.YEAR_BASE_AMOUNT END AS base_accum
    FROM intervals i
    CROSS JOIN params pm
    LEFT JOIN latest_prop_before_start lp
        ON i.ORIG_ACCT_ID = lp.ORIG_ACCT_ID
       AND i.interval_start = lp.interval_start
       AND lp.rn = 1
    WHERE i.interval_start < i.interval_end
),
org_ownership_span AS (
    SELECT
        ip.ORIG_ACCT_ID,
        ip.org_id,
        ip.employee_no,
        ip.employee_name,
        ip.interval_start AS eff_date,
        LEAD(ip.interval_start, 1, DATE_ADD(pm.period_end, INTERVAL 1 DAY))
            OVER (PARTITION BY ip.ORIG_ACCT_ID, ip.org_id, ip.employee_no ORDER BY ip.interval_start) AS exit_date,
        ip.KPI_PROP,
        ip.base_accum
    FROM interval_props ip
    CROSS JOIN params pm
    WHERE ip.org_id IS NOT NULL
),
daily_accum_by_org AS (
    SELECT
        a.ORIG_ACCT_ID,
        a.DATA_DT,
        o.org_id,
        o.employee_no,
        o.employee_name,
        a.accum_balance * o.KPI_PROP AS org_accum_share,
        o.eff_date,
        o.exit_date
    FROM acct_daily_accum a
    INNER JOIN org_ownership_span o
        ON a.ORIG_ACCT_ID = o.ORIG_ACCT_ID
       AND a.DATA_DT >= o.eff_date
       AND a.DATA_DT < o.exit_date
),
org_base AS (
    SELECT
        ORIG_ACCT_ID,
        org_id,
        employee_no,
        employee_name,
        SUM(base_accum * KPI_PROP) AS base_accum
    FROM org_ownership_span
    GROUP BY ORIG_ACCT_ID, org_id, employee_no, employee_name
),
org_active_accum AS (
    SELECT
        d.ORIG_ACCT_ID,
        d.DATA_DT,
        d.org_id,
        d.employee_no,
        d.employee_name,
        GREATEST(d.org_accum_share - b.base_accum, 0) AS effective_accum
    FROM daily_accum_by_org d
    INNER JOIN org_base b
        ON d.ORIG_ACCT_ID = b.ORIG_ACCT_ID
       AND d.org_id = b.org_id
       AND d.employee_no = b.employee_no
),
daily_factor AS (
    SELECT
        DATA_DT,
        DATEDIFF(DATA_DT, DATE(CONCAT(YEAR(DATA_DT), ''-01-01''))) + 1 AS day_num
    FROM (SELECT DISTINCT DATA_DT FROM acct_daily_accum) t
),
org_daily_contrib AS (
    SELECT
        a.org_id,
        a.employee_no,
        a.employee_name,
        a.DATA_DT,
        a.effective_accum / f.day_num AS daily_contrib
    FROM org_active_accum a
    INNER JOIN daily_factor f ON a.DATA_DT = f.DATA_DT
)
SELECT
    org_id,
    employee_no,
    employee_name,
    SUM(daily_contrib) AS metric_value
FROM org_daily_contrib
GROUP BY org_id, employee_no, employee_name
ORDER BY org_id, employee_no;'
        WHEN 5 THEN 'WITH params AS (
    SELECT
        DATE(CONCAT(SUBSTR(''{data_dt}'', 1, 4), ''-01-01'')) AS period_start,
        DATE(CONCAT(SUBSTR(''{data_dt}'', 1, 4), ''-12-31'')) AS period_end
),
acct_daily_accum AS (
    SELECT
        a.ECIF_CUST_ID,
        a.DATA_DT,
        a.BAL_YEAR_ACCUM AS accum_balance
    FROM shenzhen_data.i01_sz_acct_sum_d_history a
    CROSS JOIN params pm
    WHERE a.DATA_DT BETWEEN pm.period_start AND pm.period_end
      AND SUBSTR(a.MNG_ACCNT_PROD_ID, 1, 4) = ''L110''
      AND a.CCY_CD IN (''156'', ''B02'')
      AND (''{org_id}'' = '''' OR a.ACCNT_ORG_ID = ''{org_id}'')
),
prop_raw AS (
    SELECT
        p.ECIF_CUST_ID,
        p.DATA_DT AS eff_date,
        p.ACCOUNTING_ORG_ID AS org_id,
        p.employee_no,
        p.employee_name,
        p.KPI_PROP,
        p.YEAR_BASE_AMOUNT
    FROM shenzhen_data.shenzhen_prop_status p
    CROSS JOIN params pm
    WHERE p.DATA_DT <= pm.period_end
      AND p.PROP_STATUS_FLG = ''1''
),
distinct_eff_dates AS (
    SELECT DISTINCT ECIF_CUST_ID, eff_date
    FROM prop_raw
    CROSS JOIN params pm
    WHERE eff_date >= pm.period_start
),
all_starts AS (
    SELECT ECIF_CUST_ID, eff_date AS start_date FROM distinct_eff_dates
    UNION ALL
    SELECT a.ECIF_CUST_ID, pm.period_start AS start_date
    FROM (SELECT DISTINCT ECIF_CUST_ID FROM acct_daily_accum WHERE ECIF_CUST_ID IS NOT NULL) a
    CROSS JOIN params pm
    LEFT JOIN distinct_eff_dates d ON a.ECIF_CUST_ID = d.ECIF_CUST_ID
    WHERE d.ECIF_CUST_ID IS NULL
    UNION ALL
    SELECT a.ECIF_CUST_ID, pm.period_start AS start_date
    FROM (SELECT DISTINCT ECIF_CUST_ID FROM acct_daily_accum WHERE ECIF_CUST_ID IS NOT NULL) a
    CROSS JOIN params pm
    INNER JOIN distinct_eff_dates d ON a.ECIF_CUST_ID = d.ECIF_CUST_ID
    GROUP BY a.ECIF_CUST_ID, pm.period_start
    HAVING MIN(d.eff_date) > pm.period_start
),
intervals AS (
    SELECT
        ECIF_CUST_ID,
        start_date AS interval_start,
        LEAD(start_date, 1, DATE_ADD(pm.period_end, INTERVAL 1 DAY))
            OVER (PARTITION BY ECIF_CUST_ID ORDER BY start_date) AS interval_end
    FROM all_starts
    CROSS JOIN params pm
),
latest_prop_before_start AS (
    SELECT
        i.ECIF_CUST_ID,
        i.interval_start,
        p.org_id,
        p.employee_no,
        p.employee_name,
        p.KPI_PROP,
        p.YEAR_BASE_AMOUNT,
        ROW_NUMBER() OVER (
            PARTITION BY i.ECIF_CUST_ID, i.interval_start
            ORDER BY p.eff_date DESC
        ) AS rn
    FROM intervals i
    INNER JOIN prop_raw p
        ON i.ECIF_CUST_ID = p.ECIF_CUST_ID
       AND p.eff_date <= i.interval_start
),
interval_props AS (
    SELECT
        i.ECIF_CUST_ID,
        i.interval_start,
        i.interval_end,
        lp.org_id,
        lp.employee_no,
        lp.employee_name,
        lp.KPI_PROP,
        CASE WHEN i.interval_start = pm.period_start THEN 0 ELSE lp.YEAR_BASE_AMOUNT END AS base_accum
    FROM intervals i
    CROSS JOIN params pm
    LEFT JOIN latest_prop_before_start lp
        ON i.ECIF_CUST_ID = lp.ECIF_CUST_ID
       AND i.interval_start = lp.interval_start
       AND lp.rn = 1
    WHERE i.interval_start < i.interval_end
),
org_ownership_span AS (
    SELECT
        ip.ECIF_CUST_ID,
        ip.org_id,
        ip.employee_no,
        ip.employee_name,
        ip.interval_start AS eff_date,
        LEAD(ip.interval_start, 1, DATE_ADD(pm.period_end, INTERVAL 1 DAY))
            OVER (PARTITION BY ip.ECIF_CUST_ID, ip.org_id, ip.employee_no ORDER BY ip.interval_start) AS exit_date,
        ip.KPI_PROP,
        ip.base_accum
    FROM interval_props ip
    CROSS JOIN params pm
    WHERE ip.org_id IS NOT NULL
),
daily_accum_by_org AS (
    SELECT
        a.ECIF_CUST_ID,
        a.DATA_DT,
        o.org_id,
        o.employee_no,
        o.employee_name,
        a.accum_balance * o.KPI_PROP AS org_accum_share,
        o.eff_date,
        o.exit_date
    FROM acct_daily_accum a
    INNER JOIN org_ownership_span o
        ON a.ECIF_CUST_ID = o.ECIF_CUST_ID
       AND a.DATA_DT >= o.eff_date
       AND a.DATA_DT < o.exit_date
),
org_base AS (
    SELECT
        ECIF_CUST_ID,
        org_id,
        employee_no,
        employee_name,
        SUM(base_accum * KPI_PROP) AS base_accum
    FROM org_ownership_span
    GROUP BY ECIF_CUST_ID, org_id, employee_no, employee_name
),
org_active_accum AS (
    SELECT
        d.ECIF_CUST_ID,
        d.DATA_DT,
        d.org_id,
        d.employee_no,
        d.employee_name,
        GREATEST(d.org_accum_share - b.base_accum, 0) AS effective_accum
    FROM daily_accum_by_org d
    INNER JOIN org_base b
        ON d.ECIF_CUST_ID = b.ECIF_CUST_ID
       AND d.org_id = b.org_id
       AND d.employee_no = b.employee_no
),
daily_factor AS (
    SELECT
        DATA_DT,
        DATEDIFF(DATA_DT, DATE(CONCAT(YEAR(DATA_DT), ''-01-01''))) + 1 AS day_num
    FROM (SELECT DISTINCT DATA_DT FROM acct_daily_accum) t
),
org_daily_contrib AS (
    SELECT
        a.org_id,
        a.employee_no,
        a.employee_name,
        a.DATA_DT,
        a.effective_accum / f.day_num AS daily_contrib
    FROM org_active_accum a
    INNER JOIN daily_factor f ON a.DATA_DT = f.DATA_DT
)
SELECT
    org_id,
    employee_no,
    employee_name,
    SUM(daily_contrib) AS metric_value
FROM org_daily_contrib
GROUP BY org_id, employee_no, employee_name
ORDER BY org_id, employee_no;'
        WHEN 6 THEN 'WITH params AS (
    SELECT
        DATE(CONCAT(SUBSTR(''{data_dt}'', 1, 4), ''-01-01'')) AS period_start,
        DATE(CONCAT(SUBSTR(''{data_dt}'', 1, 4), ''-12-31'')) AS period_end
),
acct_daily_accum AS (
    SELECT
        p1.ECIF_CUST_ID,
        p1.DATA_DT,
        CASE
            WHEN p1.MNG_ACCNT_PROD_ID LIKE ''L11002%'' OR p1.MNG_ACCNT_PROD_ID LIKE ''L12002%'' THEN p1.BAL_YEAR_ACCUM
            WHEN (p1.MNG_ACCNT_PROD_ID LIKE ''L11001%'' OR p1.MNG_ACCNT_PROD_ID LIKE ''L12001%'')
                 AND CAST(p1.ACCT_TERM AS DECIMAL(18, 4)) <= 730 THEN p1.BAL_YEAR_ACCUM
            WHEN (p1.MNG_ACCNT_PROD_ID LIKE ''L11001%'' OR p1.MNG_ACCNT_PROD_ID LIKE ''L12001%'')
                 AND CAST(p1.ACCT_TERM AS DECIMAL(18, 4)) > 730
                 AND p1.EXEC_RATE <= p4.PARA_SCOPE THEN p1.BAL_YEAR_ACCUM
            ELSE 0
        END AS accum_balance
    FROM shenzhen_data.i01_sz_acct_sum_d_history p1
    LEFT JOIN shenzhen_data.FDL_REFL_DIM_PARAMET_CONFIG p4
        ON (CASE
                WHEN SUBSTR(p1.MNG_ACCNT_PROD_ID, 1, 6) = ''L12001'' THEN ''CORP_DEP_RT''
                WHEN SUBSTR(p1.MNG_ACCNT_PROD_ID, 1, 6) = ''L11001'' THEN ''INDIV_DEP_RT''
                ELSE ''''
            END) = p4.DIM_CD
       AND p1.INT_ST_DT >= CAST(p4.PARA_ST_VAL AS DATE)
       AND p1.INT_ST_DT < CAST(p4.PARA_END_VAL AS DATE)
       AND (CASE WHEN CAST(p1.ACCT_TERM AS DECIMAL(18, 4)) > 730 THEN ''3Y'' ELSE '''' END) = p4.PARA_CD
       AND p4.YEAR = SUBSTR(''{data_dt}'', 1, 4)
       AND p4.BIZ_TYPE_CD = ''B_DP_RT''
    CROSS JOIN params pm
    WHERE p1.DATA_DT BETWEEN pm.period_start AND pm.period_end
      AND p1.BASIS_CD IN (''D_100'')
      AND p1.CCY_CD IN (''156'', ''B02'')
      AND SUBSTR(p1.MNG_ACCNT_PROD_ID, 1, 4) = ''L110''
      AND (''{org_id}'' = '''' OR p1.ACCNT_ORG_ID = ''{org_id}'')
),
prop_raw AS (
    SELECT
        p.ECIF_CUST_ID,
        p.DATA_DT AS eff_date,
        p.ACCOUNTING_ORG_ID AS org_id,
        p.employee_no,
        p.employee_name,
        p.KPI_PROP,
        p.YEAR_BASE_AMOUNT
    FROM shenzhen_data.shenzhen_prop_status p
    CROSS JOIN params pm
    WHERE p.DATA_DT <= pm.period_end
      AND p.PROP_STATUS_FLG = ''1''
),
distinct_eff_dates AS (
    SELECT DISTINCT ECIF_CUST_ID, eff_date
    FROM prop_raw
    CROSS JOIN params pm
    WHERE eff_date >= pm.period_start
),
all_starts AS (
    SELECT ECIF_CUST_ID, eff_date AS start_date FROM distinct_eff_dates
    UNION ALL
    SELECT a.ECIF_CUST_ID, pm.period_start AS start_date
    FROM (SELECT DISTINCT ECIF_CUST_ID FROM acct_daily_accum WHERE ECIF_CUST_ID IS NOT NULL) a
    CROSS JOIN params pm
    LEFT JOIN distinct_eff_dates d ON a.ECIF_CUST_ID = d.ECIF_CUST_ID
    WHERE d.ECIF_CUST_ID IS NULL
    UNION ALL
    SELECT a.ECIF_CUST_ID, pm.period_start AS start_date
    FROM (SELECT DISTINCT ECIF_CUST_ID FROM acct_daily_accum WHERE ECIF_CUST_ID IS NOT NULL) a
    CROSS JOIN params pm
    INNER JOIN distinct_eff_dates d ON a.ECIF_CUST_ID = d.ECIF_CUST_ID
    GROUP BY a.ECIF_CUST_ID, pm.period_start
    HAVING MIN(d.eff_date) > pm.period_start
),
intervals AS (
    SELECT
        ECIF_CUST_ID,
        start_date AS interval_start,
        LEAD(start_date, 1, DATE_ADD(pm.period_end, INTERVAL 1 DAY))
            OVER (PARTITION BY ECIF_CUST_ID ORDER BY start_date) AS interval_end
    FROM all_starts
    CROSS JOIN params pm
),
latest_prop_before_start AS (
    SELECT
        i.ECIF_CUST_ID,
        i.interval_start,
        p.org_id,
        p.employee_no,
        p.employee_name,
        p.KPI_PROP,
        p.YEAR_BASE_AMOUNT,
        ROW_NUMBER() OVER (
            PARTITION BY i.ECIF_CUST_ID, i.interval_start
            ORDER BY p.eff_date DESC
        ) AS rn
    FROM intervals i
    INNER JOIN prop_raw p
        ON i.ECIF_CUST_ID = p.ECIF_CUST_ID
       AND p.eff_date <= i.interval_start
),
interval_props AS (
    SELECT
        i.ECIF_CUST_ID,
        i.interval_start,
        i.interval_end,
        lp.org_id,
        lp.employee_no,
        lp.employee_name,
        lp.KPI_PROP,
        CASE WHEN i.interval_start = pm.period_start THEN 0 ELSE lp.YEAR_BASE_AMOUNT END AS base_accum
    FROM intervals i
    CROSS JOIN params pm
    LEFT JOIN latest_prop_before_start lp
        ON i.ECIF_CUST_ID = lp.ECIF_CUST_ID
       AND i.interval_start = lp.interval_start
       AND lp.rn = 1
    WHERE i.interval_start < i.interval_end
),
org_ownership_span AS (
    SELECT
        ip.ECIF_CUST_ID,
        ip.org_id,
        ip.employee_no,
        ip.employee_name,
        ip.interval_start AS eff_date,
        LEAD(ip.interval_start, 1, DATE_ADD(pm.period_end, INTERVAL 1 DAY))
            OVER (PARTITION BY ip.ECIF_CUST_ID, ip.org_id, ip.employee_no ORDER BY ip.interval_start) AS exit_date,
        ip.KPI_PROP,
        ip.base_accum
    FROM interval_props ip
    CROSS JOIN params pm
    WHERE ip.org_id IS NOT NULL
),
daily_accum_by_org AS (
    SELECT
        a.ECIF_CUST_ID,
        a.DATA_DT,
        o.org_id,
        o.employee_no,
        o.employee_name,
        a.accum_balance * o.KPI_PROP AS org_accum_share,
        o.eff_date,
        o.exit_date
    FROM acct_daily_accum a
    INNER JOIN org_ownership_span o
        ON a.ECIF_CUST_ID = o.ECIF_CUST_ID
       AND a.DATA_DT >= o.eff_date
       AND a.DATA_DT < o.exit_date
),
org_base AS (
    SELECT
        ECIF_CUST_ID,
        org_id,
        employee_no,
        employee_name,
        SUM(base_accum * KPI_PROP) AS base_accum
    FROM org_ownership_span
    GROUP BY ECIF_CUST_ID, org_id, employee_no, employee_name
),
org_active_accum AS (
    SELECT
        d.ECIF_CUST_ID,
        d.DATA_DT,
        d.org_id,
        d.employee_no,
        d.employee_name,
        GREATEST(d.org_accum_share - b.base_accum, 0) AS effective_accum
    FROM daily_accum_by_org d
    INNER JOIN org_base b
        ON d.ECIF_CUST_ID = b.ECIF_CUST_ID
       AND d.org_id = b.org_id
       AND d.employee_no = b.employee_no
),
daily_factor AS (
    SELECT
        DATA_DT,
        DATEDIFF(DATA_DT, DATE(CONCAT(YEAR(DATA_DT), ''-01-01''))) + 1 AS day_num
    FROM (SELECT DISTINCT DATA_DT FROM acct_daily_accum) t
),
org_daily_contrib AS (
    SELECT
        a.org_id,
        a.employee_no,
        a.employee_name,
        a.DATA_DT,
        a.effective_accum / f.day_num AS daily_contrib
    FROM org_active_accum a
    INNER JOIN daily_factor f ON a.DATA_DT = f.DATA_DT
)
SELECT
    org_id,
    employee_no,
    employee_name,
    SUM(daily_contrib) AS metric_value
FROM org_daily_contrib
GROUP BY org_id, employee_no, employee_name
ORDER BY org_id, employee_no;'
        WHEN 7 THEN NULL
        WHEN 9 THEN NULL
        WHEN 10 THEN NULL
        WHEN 11 THEN NULL
        WHEN 12 THEN NULL
        WHEN 13 THEN NULL
        WHEN 14 THEN NULL
        WHEN 15 THEN NULL
        WHEN 16 THEN NULL
        WHEN 17 THEN NULL
        WHEN 18 THEN NULL
        WHEN 19 THEN NULL
        WHEN 21 THEN NULL
        WHEN 22 THEN NULL
        WHEN 23 THEN NULL
        WHEN 24 THEN NULL
        WHEN 25 THEN NULL
        WHEN 26 THEN NULL
    END AS daily_avg_sql_template,
    r.calc_mode,
    'org_id,employee_no,employee_name,metric_value,metric_value_2',
    r.org_prefix,
    r.need_org_filter,
    r.need_date_param,
    r.need_day_count_param,
    r.run_mode,
    r.data_source_desc,
    CASE WHEN r.indicator_id IN (2, 3, 4, 5, 6) THEN 'metric_value' ELSE 'metric_value_2' END AS display_value_field,
    CASE WHEN r.indicator_id IN (2, 3, 4, 5, 6) THEN 'metric_value_2' ELSE NULL END AS compare_value_field,
    r.status,
    CONCAT(COALESCE(r.remark, ''), '；分润规则初始化生成') AS remark
FROM perf_indicator_rule r
WHERE r.is_current = 1
  AND r.indicator_id IN (2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 24, 25, 26)
ON DUPLICATE KEY UPDATE
`indicator_id` = VALUES(`indicator_id`),
`rule_version` = VALUES(`rule_version`),
`is_current` = VALUES(`is_current`),
`rule_name` = VALUES(`rule_name`),
`point_sql_template` = VALUES(`point_sql_template`),
`daily_avg_sql_template` = VALUES(`daily_avg_sql_template`),
`calc_mode` = VALUES(`calc_mode`),
`result_fields` = VALUES(`result_fields`),
`org_prefix` = VALUES(`org_prefix`),
`need_org_filter` = VALUES(`need_org_filter`),
`need_date_param` = VALUES(`need_date_param`),
`need_day_count_param` = VALUES(`need_day_count_param`),
`run_mode` = VALUES(`run_mode`),
`data_source_desc` = VALUES(`data_source_desc`),
`display_value_field` = VALUES(`display_value_field`),
`compare_value_field` = VALUES(`compare_value_field`),
`status` = VALUES(`status`),
`remark` = VALUES(`remark`),
`updated_at` = CURRENT_TIMESTAMP;
