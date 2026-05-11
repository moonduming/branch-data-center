-- 分润指标规则时点 SQL
-- 说明：
-- 1. 本文件仅整理 point_sql_template，对应结果字段统一为 org_id, employee_no, employee_name, metric_value_2
-- 2. 账号类指标统一按 ORIG_ACCT_ID 关联 shenzhen_prop_status，取不晚于 {data_dt} 的最近一期占比
-- 3. 日均个人存款-非储AUM 源表无 ORIG_ACCT_ID，改按 ECIF_CUST_ID 关联分润占比
-- 4. 原指标规则口径见 scripts/insert_perf_indicator_seed.sql


---- 日均单位存款-全口径存款
WITH base_indicator AS (
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
        pb.ACCTN_ORG_ID,
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
    vr.ACCTN_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ORIG_ACCT_ID = vr.ORIG_ACCT_ID
GROUP BY vr.ACCTN_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;

---- 日均单位存款-优质存款
WITH base_indicator AS (
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
    SELECT pb.ORIG_ACCT_ID, pb.ACCTN_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ORIG_ACCT_ID = lt.ORIG_ACCT_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCTN_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ORIG_ACCT_ID = vr.ORIG_ACCT_ID
GROUP BY vr.ACCTN_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;

---- 日均单位存款-活期存款
WITH base_indicator AS (
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
    SELECT pb.ORIG_ACCT_ID, pb.ACCTN_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ORIG_ACCT_ID = lt.ORIG_ACCT_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCTN_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ORIG_ACCT_ID = vr.ORIG_ACCT_ID
GROUP BY vr.ACCTN_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;

---- 日均个人存款-全口径存款
WITH base_indicator AS (
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
    SELECT pb.ECIF_CUST_ID, pb.ACCTN_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ECIF_CUST_ID = lt.ECIF_CUST_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCTN_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ECIF_CUST_ID = vr.ECIF_CUST_ID
GROUP BY vr.ACCTN_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;

---- 日均个人存款-优质存款
WITH base_indicator AS (
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
    SELECT pb.ECIF_CUST_ID, pb.ACCTN_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ECIF_CUST_ID = lt.ECIF_CUST_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCTN_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ECIF_CUST_ID = vr.ECIF_CUST_ID
GROUP BY vr.ACCTN_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;


---- 日均个人存款-非储AUM
WITH base_indicator AS (
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
        pb.ACCTN_ORG_ID,
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
    vr.ACCTN_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ECIF_CUST_ID = vr.ECIF_CUST_ID
GROUP BY vr.ACCTN_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;

---- 个人贷款-个人贷款（不含徽享薪易贷）
WITH base_indicator AS (
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
    SELECT pb.ECIF_CUST_ID, pb.ACCTN_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ECIF_CUST_ID = lt.ECIF_CUST_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCTN_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ECIF_CUST_ID = vr.ECIF_CUST_ID
GROUP BY vr.ACCTN_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;

---- 个人贷款-徽享薪易贷
WITH base_indicator AS (
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
    SELECT pb.ECIF_CUST_ID, pb.ACCTN_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ECIF_CUST_ID = lt.ECIF_CUST_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCTN_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ECIF_CUST_ID = vr.ECIF_CUST_ID
GROUP BY vr.ACCTN_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;

---- 个人贷款-普惠金融
WITH base_indicator AS (
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
    SELECT pb.ECIF_CUST_ID, pb.ACCTN_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ECIF_CUST_ID = lt.ECIF_CUST_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCTN_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ECIF_CUST_ID = vr.ECIF_CUST_ID
GROUP BY vr.ACCTN_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;

---- 单位贷款-公司贷款
WITH base_indicator AS (
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
    SELECT pb.ORIG_ACCT_ID, pb.ACCTN_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ORIG_ACCT_ID = lt.ORIG_ACCT_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCTN_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ORIG_ACCT_ID = vr.ORIG_ACCT_ID
GROUP BY vr.ACCTN_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;

---- 单位贷款-行标小企业贷款
WITH base_indicator AS (
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
    SELECT pb.ORIG_ACCT_ID, pb.ACCTN_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ORIG_ACCT_ID = lt.ORIG_ACCT_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCTN_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ORIG_ACCT_ID = vr.ORIG_ACCT_ID
GROUP BY vr.ACCTN_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;

---- 五大金融-普惠金融
WITH base_indicator AS (
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
    SELECT pb.ORIG_ACCT_ID, pb.ACCTN_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ORIG_ACCT_ID = lt.ORIG_ACCT_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCTN_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ORIG_ACCT_ID = vr.ORIG_ACCT_ID
GROUP BY vr.ACCTN_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;

---- 五大金融-制造业贷款
WITH base_indicator AS (
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
    SELECT pb.ORIG_ACCT_ID, pb.ACCTN_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ORIG_ACCT_ID = lt.ORIG_ACCT_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCTN_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ORIG_ACCT_ID = vr.ORIG_ACCT_ID
GROUP BY vr.ACCTN_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;

---- 五大金融-制造业中长期贷款
WITH base_indicator AS (
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
    SELECT pb.ORIG_ACCT_ID, pb.ACCTN_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ORIG_ACCT_ID = lt.ORIG_ACCT_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCTN_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ORIG_ACCT_ID = vr.ORIG_ACCT_ID
GROUP BY vr.ACCTN_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;

---- 五大金融-战略新兴企业贷款
WITH base_indicator AS (
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
    SELECT pb.ORIG_ACCT_ID, pb.ACCTN_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ORIG_ACCT_ID = lt.ORIG_ACCT_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCTN_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ORIG_ACCT_ID = vr.ORIG_ACCT_ID
GROUP BY vr.ACCTN_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;

---- 五大金融-科技型企业贷款
WITH base_indicator AS (
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
    SELECT pb.ORIG_ACCT_ID, pb.ACCTN_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ORIG_ACCT_ID = lt.ORIG_ACCT_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCTN_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ORIG_ACCT_ID = vr.ORIG_ACCT_ID
GROUP BY vr.ACCTN_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;

---- 五大金融-绿色贷款
WITH base_indicator AS (
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
    SELECT pb.ORIG_ACCT_ID, pb.ACCTN_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ORIG_ACCT_ID = lt.ORIG_ACCT_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCTN_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ORIG_ACCT_ID = vr.ORIG_ACCT_ID
GROUP BY vr.ACCTN_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;

---- 不良资产控制额-个贷
WITH base_indicator AS (
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
    SELECT pb.ECIF_CUST_ID, pb.ACCTN_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ECIF_CUST_ID = lt.ECIF_CUST_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCTN_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ECIF_CUST_ID = vr.ECIF_CUST_ID
GROUP BY vr.ACCTN_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;

---- 不良资产控制额-对公
WITH base_indicator AS (
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
    SELECT pb.ORIG_ACCT_ID, pb.ACCTN_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ORIG_ACCT_ID = lt.ORIG_ACCT_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCTN_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ORIG_ACCT_ID = vr.ORIG_ACCT_ID
GROUP BY vr.ACCTN_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;

---- 不良资产控制额-小企业
WITH base_indicator AS (
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
    SELECT pb.ORIG_ACCT_ID, pb.ACCTN_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ORIG_ACCT_ID = lt.ORIG_ACCT_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCTN_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ORIG_ACCT_ID = vr.ORIG_ACCT_ID
GROUP BY vr.ACCTN_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;

---- 逾期贷款控制额-个贷
WITH base_indicator AS (
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
    SELECT pb.ECIF_CUST_ID, pb.ACCTN_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ECIF_CUST_ID = lt.ECIF_CUST_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCTN_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ECIF_CUST_ID = vr.ECIF_CUST_ID
GROUP BY vr.ACCTN_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;

---- 逾期贷款控制额-对公
WITH base_indicator AS (
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
    SELECT pb.ORIG_ACCT_ID, pb.ACCTN_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ORIG_ACCT_ID = lt.ORIG_ACCT_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCTN_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ORIG_ACCT_ID = vr.ORIG_ACCT_ID
GROUP BY vr.ACCTN_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;

---- 逾期贷款控制额-小企业
WITH base_indicator AS (
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
    SELECT pb.ORIG_ACCT_ID, pb.ACCTN_ORG_ID, pb.employee_no, pb.employee_name, pb.KPI_PROP
    FROM shenzhen_data.shenzhen_prop_status pb
    INNER JOIN latest_time lt
        ON pb.ORIG_ACCT_ID = lt.ORIG_ACCT_ID
       AND pb.DATA_DT = lt.max_data_dt
    WHERE pb.PROP_STATUS_FLG = ''1''
)
SELECT
    vr.ACCTN_ORG_ID AS org_id,
    vr.employee_no,
    vr.employee_name,
    SUM(bi.metric_value_2 * vr.KPI_PROP) AS metric_value_2
FROM base_indicator bi
INNER JOIN valid_ratio vr
    ON bi.ORIG_ACCT_ID = vr.ORIG_ACCT_ID
GROUP BY vr.ACCTN_ORG_ID, vr.employee_no, vr.employee_name
ORDER BY org_id, employee_no;
