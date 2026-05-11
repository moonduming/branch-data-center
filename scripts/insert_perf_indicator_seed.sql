-- 指标定义与指标规则初始化脚本
-- 来源：指标计算口径.txt
-- 整理说明：
-- 1. 一级指标使用银行给定编码：440 / 380 / 480
-- 2. 仅保留两级结构：一级为父指标，二级为直接关联规则的叶子指标
-- 3. 叶子指标沿用原三级编码，例如 4400101 / 3800302
-- 4. SQL 模板统一支持 {data_dt} / {day_count} / {org_id} 三个参数
-- 5. org_id 采用可选过滤：当 {org_id} = '' 时返回全部机构，否则返回指定机构
-- 6. 因执行时目标表为空，perf_indicator / perf_indicator_rule 主键均按 1 开始顺序写入

INSERT INTO `perf_indicator`
(`id`, `indicator_code`, `indicator_name`, `parent_id`, `category_code`, `category_name`, `sort_no`, `status`, `description`, `remark`)
VALUES
(1, '440', '发展转型类指标', NULL, '440', '发展转型类指标', 1, '01', '一级指标分类', '根据指标计算口径整理生成'),
(2, '4400101', '日均单位存款-全口径存款', 1, '440', '发展转型类指标', 4400101, '01', '二级叶子指标', '根据指标计算口径整理生成'),
(3, '4400102', '日均单位存款-优质存款', 1, '440', '发展转型类指标', 4400102, '01', '二级叶子指标', '根据指标计算口径整理生成'),
(4, '4400103', '日均单位存款-活期存款', 1, '440', '发展转型类指标', 4400103, '01', '二级叶子指标', '根据指标计算口径整理生成'),
(5, '4400201', '日均个人存款-全口径存款', 1, '440', '发展转型类指标', 4400201, '01', '二级叶子指标', '根据指标计算口径整理生成'),
(6, '4400202', '日均个人存款-优质存款', 1, '440', '发展转型类指标', 4400202, '01', '二级叶子指标', '根据指标计算口径整理生成'),
(7, '4400203', '日均个人存款-非储AUM', 1, '440', '发展转型类指标', 4400203, '01', '二级叶子指标', '根据指标计算口径整理生成'),
(8, '380', '社会责任类指标', NULL, '380', '社会责任类指标', 8, '01', '一级指标分类', '根据指标计算口径整理生成'),
(9, '3800101', '个人贷款-个人贷款（不含徽享薪易贷）', 8, '380', '社会责任类指标', 3800101, '01', '二级叶子指标', '根据指标计算口径整理生成'),
(10, '3800102', '个人贷款-徽享薪易贷', 8, '380', '社会责任类指标', 3800102, '01', '二级叶子指标', '根据指标计算口径整理生成'),
(11, '3800103', '个人贷款-普惠金融', 8, '380', '社会责任类指标', 3800103, '01', '二级叶子指标', '根据指标计算口径整理生成'),
(12, '3800201', '单位贷款-公司贷款', 8, '380', '社会责任类指标', 3800201, '01', '二级叶子指标', '根据指标计算口径整理生成'),
(13, '3800202', '单位贷款-行标小企业贷款', 8, '380', '社会责任类指标', 3800202, '01', '二级叶子指标', '根据指标计算口径整理生成'),
(14, '3800301', '五大金融-普惠金融', 8, '380', '社会责任类指标', 3800301, '01', '二级叶子指标', '根据指标计算口径整理生成'),
(15, '3800302', '五大金融-制造业贷款', 8, '380', '社会责任类指标', 3800302, '01', '二级叶子指标', '根据指标计算口径整理生成'),
(16, '3800303', '五大金融-制造业中长期贷款', 8, '380', '社会责任类指标', 3800303, '01', '二级叶子指标', '根据指标计算口径整理生成'),
(17, '3800304', '五大金融-战略新兴企业贷款', 8, '380', '社会责任类指标', 3800304, '01', '二级叶子指标', '根据指标计算口径整理生成'),
(18, '3800305', '五大金融-科技型企业贷款', 8, '380', '社会责任类指标', 3800305, '01', '二级叶子指标', '根据指标计算口径整理生成'),
(19, '3800306', '五大金融-绿色贷款', 8, '380', '社会责任类指标', 3800306, '01', '二级叶子指标', '根据指标计算口径整理生成'),
(20, '480', '风险管理类指标', NULL, '480', '风险管理类指标', 20, '01', '一级指标分类', '根据指标计算口径整理生成'),
(21, '4800101', '不良资产控制额-个贷', 20, '480', '风险管理类指标', 4800101, '01', '二级叶子指标', '根据指标计算口径整理生成'),
(22, '4800102', '不良资产控制额-对公', 20, '480', '风险管理类指标', 4800102, '01', '二级叶子指标', '根据指标计算口径整理生成'),
(23, '4800103', '不良资产控制额-小企业', 20, '480', '风险管理类指标', 4800103, '01', '二级叶子指标', '根据指标计算口径整理生成'),
(24, '4800201', '逾期贷款控制额-个贷', 20, '480', '风险管理类指标', 4800201, '01', '二级叶子指标', '根据指标计算口径整理生成'),
(25, '4800202', '逾期贷款控制额-对公', 20, '480', '风险管理类指标', 4800202, '01', '二级叶子指标', '根据指标计算口径整理生成'),
(26, '4800203', '逾期贷款控制额-小企业', 20, '480', '风险管理类指标', 4800203, '01', '二级叶子指标', '根据指标计算口径整理生成')
ON DUPLICATE KEY UPDATE
`indicator_code` = VALUES(`indicator_code`),
`indicator_name` = VALUES(`indicator_name`),
`parent_id` = VALUES(`parent_id`),
`category_code` = VALUES(`category_code`),
`category_name` = VALUES(`category_name`),
`sort_no` = VALUES(`sort_no`),
`status` = VALUES(`status`),
`description` = VALUES(`description`),
`remark` = VALUES(`remark`);


INSERT INTO `perf_indicator_rule`
(`id`, `indicator_id`, `rule_version`, `is_current`, `rule_name`, `sql_template`, `calc_mode`, `result_fields`, `org_prefix`, `need_org_filter`, `need_date_param`, `need_day_count_param`, `run_mode`, `data_source_desc`, `status`, `remark`)
VALUES
(1, 2, 1, 1, '日均单位存款-全口径存款', 'SELECT
    MNG_ORG_ID AS org_id,
    SUM(BAL_YEAR_ACCUM) / {day_count} AS metric_value,
    SUM(CUR_BAL) AS metric_value_2
FROM shenzhen_data.i01_sz_acct_sum_d_history
WHERE DATA_DT = ''{data_dt}''
  AND SUBSTR(MNG_ACCNT_PROD_ID, 1, 4) = ''L120''
  AND CCY_CD IN (''156'', ''B02'')
  AND (''{org_id}'' = '''' OR MNG_ORG_ID = ''{org_id}'')
GROUP BY MNG_ORG_ID', 'single_value', 'org_id,metric_value,metric_value_2', '0100', 1, 1, 1, 'all_org', 'shenzhen_data.i01_sz_acct_sum_d', '01', '原始口径同时返回时点余额和年日均积数，metric_value 取年日均，metric_value_2 取时点余额'),
 (2, 3, 1, 1, '日均单位存款-优质存款', 'SELECT
    P1.ACCNT_ORG_ID AS org_id,
    SUM(
        CASE
            WHEN P1.MNG_ACCNT_PROD_ID LIKE ''L11002%'' OR P1.MNG_ACCNT_PROD_ID LIKE ''L12002%'' THEN 1
            WHEN (P1.MNG_ACCNT_PROD_ID LIKE ''L11001%'' OR P1.MNG_ACCNT_PROD_ID LIKE ''L12001%'')
                 AND CAST(P1.ACCT_TERM AS DECIMAL(18, 4)) <= 730 THEN 1
            WHEN (P1.MNG_ACCNT_PROD_ID LIKE ''L11001%'' OR P1.MNG_ACCNT_PROD_ID LIKE ''L12001%'')
                 AND CAST(P1.ACCT_TERM AS DECIMAL(18, 4)) > 730
                 AND P1.EXEC_RATE <= P4.PARA_SCOPE THEN 1
            ELSE 0
        END * P1.BAL_YEAR_ACCUM
    ) / {day_count} AS metric_value,
    SUM(
        CASE
            WHEN P1.MNG_ACCNT_PROD_ID LIKE ''L11002%'' OR P1.MNG_ACCNT_PROD_ID LIKE ''L12002%'' THEN 1
            WHEN (P1.MNG_ACCNT_PROD_ID LIKE ''L11001%'' OR P1.MNG_ACCNT_PROD_ID LIKE ''L12001%'')
                 AND CAST(P1.ACCT_TERM AS DECIMAL(18, 4)) <= 730 THEN 1
            WHEN (P1.MNG_ACCNT_PROD_ID LIKE ''L11001%'' OR P1.MNG_ACCNT_PROD_ID LIKE ''L12001%'')
                 AND CAST(P1.ACCT_TERM AS DECIMAL(18, 4)) > 730
                 AND P1.EXEC_RATE <= P4.PARA_SCOPE THEN 1
            ELSE 0
        END * P1.CUR_BAL
    ) AS metric_value_2
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
GROUP BY P1.ACCNT_ORG_ID', 'single_value', 'org_id,metric_value,metric_value_2', NULL, 1, 1, 1, 'all_org', 'shenzhen_data.i01_sz_acct_sum_m; shenzhen_data.fdl_refl_dim_paramet_config', '01', 'metric_value 取年日均，metric_value_2 取时点余额'),
(3, 4, 1, 1, '日均单位存款-活期存款', 'SELECT
    MNG_ORG_ID AS org_id,
    SUM(BAL_YEAR_ACCUM) / {day_count} AS metric_value,
    SUM(CUR_BAL) AS metric_value_2
FROM shenzhen_data.i01_sz_acct_sum_d_history
WHERE DATA_DT = ''{data_dt}''
  AND SUBSTR(MNG_ACCNT_PROD_ID, 1, 4) = ''L120''
  AND CCY_CD IN (''156'', ''B02'')
  AND FIX_CUR_FLG = ''0''
  AND (''{org_id}'' = '''' OR MNG_ORG_ID = ''{org_id}'')
GROUP BY MNG_ORG_ID', 'single_value', 'org_id,metric_value,metric_value_2', '0100', 1, 1, 1, 'all_org', 'shenzhen_data.i01_sz_acct_sum_d', '01', 'metric_value 取年日均，metric_value_2 取时点余额'),
(4, 5, 1, 1, '日均个人存款-全口径存款', 'SELECT
    MNG_ORG_ID AS org_id,
    SUM(BAL_YEAR_ACCUM) / {day_count} AS metric_value,
    SUM(CUR_BAL) AS metric_value_2
FROM shenzhen_data.i01_sz_acct_sum_d_history
WHERE DATA_DT = ''{data_dt}''
  AND SUBSTR(MNG_ACCNT_PROD_ID, 1, 4) = ''L110''
  AND CCY_CD IN (''156'', ''B02'')
  AND (''{org_id}'' = '''' OR MNG_ORG_ID = ''{org_id}'')
GROUP BY MNG_ORG_ID', 'single_value', 'org_id,metric_value,metric_value_2', '0100', 1, 1, 1, 'all_org', 'shenzhen_data.i01_sz_acct_sum_d', '01', 'metric_value 取年日均，metric_value_2 取时点余额'),
 (5, 6, 1, 1, '日均个人存款-优质存款', 'SELECT
    P1.ACCNT_ORG_ID AS org_id,
    SUM(
        CASE
            WHEN P1.MNG_ACCNT_PROD_ID LIKE ''L11002%'' OR P1.MNG_ACCNT_PROD_ID LIKE ''L12002%'' THEN 1
            WHEN (P1.MNG_ACCNT_PROD_ID LIKE ''L11001%'' OR P1.MNG_ACCNT_PROD_ID LIKE ''L12001%'')
                 AND CAST(P1.ACCT_TERM AS DECIMAL(18, 4)) <= 730 THEN 1
            WHEN (P1.MNG_ACCNT_PROD_ID LIKE ''L11001%'' OR P1.MNG_ACCNT_PROD_ID LIKE ''L12001%'')
                 AND CAST(P1.ACCT_TERM AS DECIMAL(18, 4)) > 730
                 AND P1.EXEC_RATE <= P4.PARA_SCOPE THEN 1
            ELSE 0
        END * P1.BAL_YEAR_ACCUM
    ) / {day_count} AS metric_value,
    SUM(
        CASE
            WHEN P1.MNG_ACCNT_PROD_ID LIKE ''L11002%'' OR P1.MNG_ACCNT_PROD_ID LIKE ''L12002%'' THEN 1
            WHEN (P1.MNG_ACCNT_PROD_ID LIKE ''L11001%'' OR P1.MNG_ACCNT_PROD_ID LIKE ''L12001%'')
                 AND CAST(P1.ACCT_TERM AS DECIMAL(18, 4)) <= 730 THEN 1
            WHEN (P1.MNG_ACCNT_PROD_ID LIKE ''L11001%'' OR P1.MNG_ACCNT_PROD_ID LIKE ''L12001%'')
                 AND CAST(P1.ACCT_TERM AS DECIMAL(18, 4)) > 730
                 AND P1.EXEC_RATE <= P4.PARA_SCOPE THEN 1
            ELSE 0
        END * P1.CUR_BAL
    ) AS metric_value_2
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
GROUP BY P1.ACCNT_ORG_ID', 'single_value', 'org_id,metric_value,metric_value_2', NULL, 1, 1, 1, 'all_org', 'shenzhen_data.i01_sz_acct_sum_m; shenzhen_data.fdl_refl_dim_paramet_config', '01', 'metric_value 取年日均，metric_value_2 取时点余额'),
 (6, 7, 1, 1, '日均个人存款-非储AUM', 'SELECT
    ACCNT_ORG_ID AS org_id,
    SUM(NONSAVING_SCALE_YEAR_DAY_AVG_BAL) AS metric_value,
    SUM(NONSAVING_SCALE) AS metric_value_2
FROM shenzhen_data.i01_sz_indiv_asset_data_tbl_history
WHERE DATA_DT = ''{data_dt}''
  AND (''{org_id}'' = '''' OR ACCNT_ORG_ID = ''{org_id}'')
GROUP BY ACCNT_ORG_ID', 'single_value', 'org_id,metric_value,metric_value_2', NULL, 1, 1, 0, 'all_org', 'shenzhen_data.i01_sz_indiv_asset_data_tbl', '01', '原始口径使用年日均非储字段'),
(7, 9, 1, 1, '个人贷款-个人贷款（不含徽享薪易贷）', 'SELECT
    ACCNT_ORG_ID AS org_id,
    SUM(CUR_BAL) AS metric_value_2
FROM shenzhen_data.i01_sz_acct_sum_d_history
WHERE DATA_DT = ''{data_dt}''
  AND SUBSTR(MNG_ACCNT_PROD_ID, 1, 4) = ''A110''
  AND MNG_ACCNT_PROD_ID <> ''A11001014001''
  AND (''{org_id}'' = '''' OR ACCNT_ORG_ID = ''{org_id}'')
GROUP BY ACCNT_ORG_ID', 'single_value', 'org_id,metric_value,metric_value_2', NULL, 1, 1, 1, 'all_org', 'shenzhen_data.i01_sz_acct_sum_d', '01', 'metric_value 取年日均，metric_value_2 取当前余额'),
(8, 10, 1, 1, '个人贷款-徽享薪易贷', 'SELECT
    ACCNT_ORG_ID AS org_id,
    SUM(CUR_BAL) AS metric_value_2
FROM shenzhen_data.i01_sz_acct_sum_d_history
WHERE DATA_DT = ''{data_dt}''
  AND SUBSTR(MNG_ACCNT_PROD_ID, 1, 4) = ''A110''
  AND MNG_ACCNT_PROD_ID = ''A11001014001''
  AND (''{org_id}'' = '''' OR ACCNT_ORG_ID = ''{org_id}'')
GROUP BY ACCNT_ORG_ID', 'single_value', 'org_id,metric_value,metric_value_2', NULL, 1, 1, 1, 'all_org', 'shenzhen_data.i01_sz_acct_sum_d', '01', '原文产品号存在明显截断，按上下文修正为 A11001014001；metric_value 取年日均，metric_value_2 取当前余额'),
 (9, 11, 1, 1, '个人贷款-普惠金融', 'SELECT
    ACCNT_ORG_ID AS org_id,
    SUM(CUR_BAL) AS metric_value_2
FROM shenzhen_data.i01_sz_acct_sum_d_history
WHERE DATA_DT = ''{data_dt}''
  AND SUBSTR(MNG_ACCNT_PROD_ID, 1, 4) = ''A110''
  AND INCR_LOAN_FLG = ''1''
  AND CCY_CD IN (''156'', ''B02'')
  AND (''{org_id}'' = '''' OR ACCNT_ORG_ID = ''{org_id}'')
GROUP BY ACCNT_ORG_ID', 'single_value', 'org_id,metric_value_2', NULL, 1, 1, 0, 'all_org', 'shenzhen_data.i01_sz_acct_sum_d', '01', 'metric_value_2 取时点余额'),
 (10, 12, 1, 1, '单位贷款-公司贷款', 'SELECT
    ACCNT_ORG_ID AS org_id,
    SUM(CUR_BAL + INT_ADJUST_AMT) AS metric_value_2
FROM shenzhen_data.i01_sz_acct_sum_d_history
WHERE DATA_DT = ''{data_dt}''
  AND LINE_ID <> ''L0103''
  AND CCY_CD IN (''156'', ''B02'')
  AND (MNG_ACCNT_PROD_ID LIKE ''A12001%'' OR MNG_ACCNT_PROD_ID LIKE ''A12002%'' OR MNG_ACCNT_PROD_ID LIKE ''A12003%'' OR MNG_ACCNT_PROD_ID LIKE ''A12005%'')
  AND MNG_ACCNT_PROD_ID NOT IN (''A12002015001'', ''A12004001005'', ''A12004002004'')
  AND (''{org_id}'' = '''' OR ACCNT_ORG_ID = ''{org_id}'')
GROUP BY ACCNT_ORG_ID', 'single_value', 'org_id,metric_value_2', NULL, 1, 1, 0, 'all_org', 'shenzhen_data.i01_sz_acct_sum_d', '01', 'metric_value_2 取时点余额'),
 (11, 13, 1, 1, '单位贷款-行标小企业贷款', 'SELECT
    ACCNT_ORG_ID AS org_id,
    SUM(CUR_BAL + INT_ADJUST_AMT) AS metric_value_2
FROM shenzhen_data.i01_sz_acct_sum_d_history
WHERE DATA_DT = ''{data_dt}''
  AND LINE_ID = ''L0103''
  AND CCY_CD IN (''156'', ''B02'')
  AND (MNG_ACCNT_PROD_ID LIKE ''A12001%'' OR MNG_ACCNT_PROD_ID LIKE ''A12002%'' OR MNG_ACCNT_PROD_ID LIKE ''A12003%'' OR MNG_ACCNT_PROD_ID LIKE ''A12005%'')
  AND MNG_ACCNT_PROD_ID NOT IN (''A12002015001'', ''A12004001005'', ''A12004002004'')
  AND (''{org_id}'' = '''' OR ACCNT_ORG_ID = ''{org_id}'')
GROUP BY ACCNT_ORG_ID', 'single_value', 'org_id,metric_value_2', NULL, 1, 1, 0, 'all_org', 'shenzhen_data.i01_sz_acct_sum_d', '01', 'metric_value_2 取时点余额'),
(12, 14, 1, 1, '五大金融-普惠金融', 'SELECT
    ACCNT_ORG_ID AS org_id,
    SUM(CUR_BAL + INT_ADJUST_AMT) AS metric_value_2
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
GROUP BY ACCNT_ORG_ID', 'single_value', 'org_id,metric_value_2', NULL, 1, 1, 0, 'all_org', 'shenzhen_data.i01_sz_acct_sum_d', '01', 'metric_value_2 取时点余额'),
 (13, 15, 1, 1, '五大金融-制造业贷款', 'SELECT
    ACCNT_ORG_ID AS org_id,
    SUM(CUR_BAL + INT_ADJUST_AMT) AS metric_value_2
FROM shenzhen_data.i01_sz_acct_sum_d_history
WHERE DATA_DT = ''{data_dt}''
  AND MANUF_INDUS_LOAN_FLG = ''1''
  AND CCY_CD IN (''156'', ''B02'')
  AND (''{org_id}'' = '''' OR ACCNT_ORG_ID = ''{org_id}'')
GROUP BY ACCNT_ORG_ID', 'single_value', 'org_id,metric_value_2', NULL, 1, 1, 0, 'all_org', 'shenzhen_data.i01_sz_acct_sum_d', '01', 'metric_value_2 取时点余额'),
 (14, 16, 1, 1, '五大金融-制造业中长期贷款', 'SELECT
    ACCNT_ORG_ID AS org_id,
    SUM(CUR_BAL + INT_ADJUST_AMT) AS metric_value_2
FROM shenzhen_data.i01_sz_acct_sum_d_history
WHERE DATA_DT = ''{data_dt}''
  AND MANUF_INDUS_LONGTERM_LOAN_FLG = ''1''
  AND CCY_CD IN (''156'', ''B02'')
  AND (''{org_id}'' = '''' OR ACCNT_ORG_ID = ''{org_id}'')
GROUP BY ACCNT_ORG_ID', 'single_value', 'org_id,metric_value_2', NULL, 1, 1, 0, 'all_org', 'shenzhen_data.i01_sz_acct_sum_d', '01', 'metric_value_2 取时点余额'),
 (15, 17, 1, 1, '五大金融-战略新兴企业贷款', 'SELECT
    ACCNT_ORG_ID AS org_id,
    SUM(CUR_BAL + INT_ADJUST_AMT) AS metric_value_2
FROM shenzhen_data.i01_sz_acct_sum_d_history
WHERE DATA_DT = ''{data_dt}''
  AND STRA_EMERGE_INDUS_FLG = ''1''
  AND CCY_CD IN (''156'', ''B02'')
  AND (''{org_id}'' = '''' OR ACCNT_ORG_ID = ''{org_id}'')
GROUP BY ACCNT_ORG_ID', 'single_value', 'org_id,metric_value_2', NULL, 1, 1, 0, 'all_org', 'shenzhen_data.i01_sz_acct_sum_d', '01', 'metric_value_2 取时点余额'),
 (16, 18, 1, 1, '五大金融-科技型企业贷款', 'SELECT
    ACCNT_ORG_ID AS org_id,
    SUM(CUR_BAL + INT_ADJUST_AMT) AS metric_value_2
FROM shenzhen_data.i01_sz_acct_sum_d_history
WHERE DATA_DT = ''{data_dt}''
  AND TECH_INNO_LOAN_FLG = ''1''
  AND CCY_CD IN (''156'', ''B02'')
  AND (''{org_id}'' = '''' OR ACCNT_ORG_ID = ''{org_id}'')
GROUP BY ACCNT_ORG_ID', 'single_value', 'org_id,metric_value_2', NULL, 1, 1, 0, 'all_org', 'shenzhen_data.i01_sz_acct_sum_d', '01', 'metric_value_2 取时点余额'),
 (17, 19, 1, 1, '五大金融-绿色贷款', 'SELECT
    ACCNT_ORG_ID AS org_id,
    SUM(CUR_BAL + INT_ADJUST_AMT) AS metric_value_2
FROM shenzhen_data.i01_sz_acct_sum_d_history
WHERE DATA_DT = ''{data_dt}''
  AND GREEN_LOAN_FLG = ''1''
  AND CCY_CD IN (''156'', ''B02'')
  AND (''{org_id}'' = '''' OR ACCNT_ORG_ID = ''{org_id}'')
GROUP BY ACCNT_ORG_ID', 'single_value', 'org_id,metric_value_2', NULL, 1, 1, 0, 'all_org', 'shenzhen_data.i01_sz_acct_sum_d', '01', 'metric_value_2 取时点余额'),
(18, 21, 1, 1, '不良资产控制额-个贷', 'SELECT
    ACCNT_ORG_ID AS org_id,
    SUM(BAD_LOAN_AMT) AS metric_value_2
FROM shenzhen_data.i01_sz_acct_sum_d_history
WHERE DATA_DT = ''{data_dt}''
  AND SUBSTR(MNG_ACCNT_PROD_ID, 1, 4) = ''A110''
  AND MNG_ACCNT_PROD_ID <> ''A11001014001''
  AND (''{org_id}'' = '''' OR ACCNT_ORG_ID = ''{org_id}'')
GROUP BY ACCNT_ORG_ID', 'single_value', 'org_id,metric_value_2', NULL, 1, 1, 0, 'all_org', 'shenzhen_data.i01_sz_acct_sum_d', '01', 'metric_value_2 取时点余额'),
 (19, 22, 1, 1, '不良资产控制额-对公', 'SELECT
    ACCNT_ORG_ID AS org_id,
    SUM(BAD_LOAN_AMT) AS metric_value_2
FROM shenzhen_data.i01_sz_acct_sum_d_history
WHERE DATA_DT = ''{data_dt}''
  AND LINE_ID <> ''L0103''
  AND CCY_CD IN (''156'', ''B02'')
  AND (MNG_ACCNT_PROD_ID LIKE ''A12001%'' OR MNG_ACCNT_PROD_ID LIKE ''A12002%'' OR MNG_ACCNT_PROD_ID LIKE ''A12003%'' OR MNG_ACCNT_PROD_ID LIKE ''A12005%'')
  AND MNG_ACCNT_PROD_ID NOT IN (''A12002015001'', ''A12004001005'', ''A12004002004'')
  AND (''{org_id}'' = '''' OR ACCNT_ORG_ID = ''{org_id}'')
GROUP BY ACCNT_ORG_ID', 'single_value', 'org_id,metric_value_2', NULL, 1, 1, 0, 'all_org', 'shenzhen_data.i01_sz_acct_sum_d', '01', 'metric_value_2 取时点余额'),
 (20, 23, 1, 1, '不良资产控制额-小企业', 'SELECT
    ACCNT_ORG_ID AS org_id,
    SUM(BAD_LOAN_AMT) AS metric_value_2
FROM shenzhen_data.i01_sz_acct_sum_d_history
WHERE DATA_DT = ''{data_dt}''
  AND LINE_ID = ''L0103''
  AND CCY_CD IN (''156'', ''B02'')
  AND (MNG_ACCNT_PROD_ID LIKE ''A12001%'' OR MNG_ACCNT_PROD_ID LIKE ''A12002%'' OR MNG_ACCNT_PROD_ID LIKE ''A12003%'' OR MNG_ACCNT_PROD_ID LIKE ''A12005%'')
  AND MNG_ACCNT_PROD_ID NOT IN (''A12002015001'', ''A12004001005'', ''A12004002004'')
  AND (''{org_id}'' = '''' OR ACCNT_ORG_ID = ''{org_id}'')
GROUP BY ACCNT_ORG_ID', 'single_value', 'org_id,metric_value_2', NULL, 1, 1, 0, 'all_org', 'shenzhen_data.i01_sz_acct_sum_d', '01', 'metric_value_2 取时点余额'),
 (21, 24, 1, 1, '逾期贷款控制额-个贷', 'SELECT
    ACCNT_ORG_ID AS org_id,
    SUM(CUR_BAL) AS metric_value_2
FROM shenzhen_data.i01_sz_acct_sum_d_history
WHERE DATA_DT = ''{data_dt}''
  AND SUBSTR(MNG_ACCNT_PROD_ID, 1, 4) = ''A110''
  AND MNG_ACCNT_PROD_ID <> ''A11001014001''
  AND OVERDUE_FLG = ''1''
  AND (''{org_id}'' = '''' OR ACCNT_ORG_ID = ''{org_id}'')
GROUP BY ACCNT_ORG_ID', 'single_value', 'org_id,metric_value_2', NULL, 1, 1, 0, 'all_org', 'shenzhen_data.i01_sz_acct_sum_d', '01', 'metric_value_2 取时点余额'),
 (22, 25, 1, 1, '逾期贷款控制额-对公', 'SELECT
    ACCNT_ORG_ID AS org_id,
    SUM(CUR_BAL + INT_ADJUST_AMT) AS metric_value_2
FROM shenzhen_data.i01_sz_acct_sum_d_history
WHERE DATA_DT = ''{data_dt}''
  AND LINE_ID <> ''L0103''
  AND CCY_CD IN (''156'', ''B02'')
  AND (MNG_ACCNT_PROD_ID LIKE ''A12001%'' OR MNG_ACCNT_PROD_ID LIKE ''A12002%'' OR MNG_ACCNT_PROD_ID LIKE ''A12003%'' OR MNG_ACCNT_PROD_ID LIKE ''A12005%'')
  AND MNG_ACCNT_PROD_ID NOT IN (''A12002015001'', ''A12004001005'', ''A12004002004'')
  AND OVERDUE_FLG = ''1''
  AND (''{org_id}'' = '''' OR ACCNT_ORG_ID = ''{org_id}'')
GROUP BY ACCNT_ORG_ID', 'single_value', 'org_id,metric_value_2', NULL, 1, 1, 0, 'all_org', 'shenzhen_data.i01_sz_acct_sum_d', '01', 'metric_value_2 取时点余额'),
 (23, 26, 1, 1, '逾期贷款控制额-小企业', 'SELECT
    ACCNT_ORG_ID AS org_id,
    SUM(CUR_BAL + INT_ADJUST_AMT) AS metric_value_2
FROM shenzhen_data.i01_sz_acct_sum_d_history
WHERE DATA_DT = ''{data_dt}''
  AND LINE_ID = ''L0103''
  AND CCY_CD IN (''156'', ''B02'')
  AND (MNG_ACCNT_PROD_ID LIKE ''A12001%'' OR MNG_ACCNT_PROD_ID LIKE ''A12002%'' OR MNG_ACCNT_PROD_ID LIKE ''A12003%'' OR MNG_ACCNT_PROD_ID LIKE ''A12005%'')
  AND MNG_ACCNT_PROD_ID NOT IN (''A12002015001'', ''A12004001005'', ''A12004002004'')
  AND OVERDUE_FLG = ''1''
  AND (''{org_id}'' = '''' OR ACCNT_ORG_ID = ''{org_id}'')
GROUP BY ACCNT_ORG_ID', 'single_value', 'org_id,metric_value_2', NULL, 1, 1, 0, 'all_org', 'shenzhen_data.i01_sz_acct_sum_d', '01', 'metric_value_2 取时点余额')
ON DUPLICATE KEY UPDATE
`indicator_id` = VALUES(`indicator_id`),
`rule_version` = VALUES(`rule_version`),
`is_current` = VALUES(`is_current`),
`rule_name` = VALUES(`rule_name`),
`sql_template` = VALUES(`sql_template`),
`calc_mode` = VALUES(`calc_mode`),
`result_fields` = VALUES(`result_fields`),
`org_prefix` = VALUES(`org_prefix`),
`need_org_filter` = VALUES(`need_org_filter`),
`need_date_param` = VALUES(`need_date_param`),
`need_day_count_param` = VALUES(`need_day_count_param`),
`run_mode` = VALUES(`run_mode`),
`data_source_desc` = VALUES(`data_source_desc`),
`status` = VALUES(`status`),
`remark` = VALUES(`remark`);
