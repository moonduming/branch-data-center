from django.db import models


class PropStatusFlg(models.TextChoices):
    """占比生效状态"""
    YES = "1", "是"
    NO = "0", "否"
    INVALID = "2", "失效"


class ShenzhenPropStatus(models.Model):
    """占比情况表"""
    id = models.BigAutoField(primary_key=True, db_column="id", verbose_name="主键ID")
    process_instance_id = models.BigIntegerField(
        db_column="PROCESS_INSTANCE_ID",
        null=True,
        blank=True,
        verbose_name="流程实例ID",
    )
    data_dt = models.DateField(
        db_column="DATA_DT",
        null=True,
        blank=True,
        verbose_name="生效日期",
    )
    ecif_cust_id = models.CharField(
        db_column="ECIF_CUST_ID",
        max_length=10,
        null=True,
        blank=True,
        verbose_name="ECIF客户编号",
    )
    orig_acct_id = models.CharField(
        db_column="ORIG_ACCT_ID",
        max_length=60,
        null=True,
        blank=True,
        verbose_name="原始账号",
    )
    cust_name = models.CharField(
        db_column="CUST_NAME",
        max_length=450,
        null=True,
        blank=True,
        verbose_name="客户名称",
    )
    claim_org_id = models.CharField(
        db_column="CLAIM_ORG_ID",
        max_length=8,
        null=True,
        blank=True,
        verbose_name="认领机构编号",
    )
    claim_org_name = models.CharField(
        db_column="CLAIM_ORG_NAME",
        max_length=100,
        null=True,
        blank=True,
        verbose_name="认领机构名称",
    )
    accounting_org_id = models.CharField(
        db_column="ACCOUNTING_ORG_ID",
        max_length=8,
        null=True,
        blank=True,
        verbose_name="核算机构编号",
    )
    accounting_org_name = models.CharField(
        db_column="ACCOUNTING_ORG_NAME",
        max_length=100,
        null=True,
        blank=True,
        verbose_name="核算机构名称",
    )
    line_org_code = models.CharField(
        db_column="LINE_ORG_CODE",
        max_length=32,
        null=True,
        blank=True,
        verbose_name="条线机构编码",
    )
    employee_no = models.CharField(
        db_column="employee_no",
        max_length=32,
        null=True,
        blank=True,
        verbose_name="认领员工编号",
    )
    employee_name = models.CharField(
        db_column="employee_name",
        max_length=50,
        null=True,
        blank=True,
        verbose_name="认领员工姓名",
    )
    kpi_prop = models.DecimalField(
        db_column="KPI_PROP",
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
        verbose_name="业绩占比",
    )
    prop_status_flg = models.CharField(
        db_column="PROP_STATUS_FLG",
        max_length=1,
        choices=PropStatusFlg.choices,
        default=PropStatusFlg.NO,
        verbose_name="占比生效状态",
    )
    apl_data_dt = models.DateTimeField(
        db_column="APL_DATA_DT",
        null=True,
        blank=True,
        verbose_name="申请时间",
    )
    pas_data_dt = models.DateTimeField(
        db_column="PAS_DATA_DT",
        null=True,
        blank=True,
        verbose_name="通过时间",
    )
    year_base_amount = models.DecimalField(
        db_column="YEAR_BASE_AMOUNT",
        max_digits=18,
        decimal_places=2,
        default=0,
        verbose_name="余额年累计基数",
    )
    genr_acct_id = models.CharField(
        db_column="GENR_ACCT_ID", 
        max_length=60, 
        verbose_name="通用账户号"
    )

    class Meta:
        managed = False
        db_table = "shenzhen_prop_status"
        verbose_name = "占比情况表"
        verbose_name_plural = "占比情况表"
        indexes = [
            models.Index(fields=["process_instance_id"], name="idx_process_instance_id"),
            models.Index(fields=["cust_name"], name="idx_cust_name"),
            models.Index(fields=["employee_no"], name="idx_employee_no"),
        ]


class BaseAcctSum(models.Model):
    """账户汇总历史表（抽象基类）"""
    id = models.BigAutoField(primary_key=True, db_column="ID", verbose_name="自增ID")
    data_dt = models.DateField(db_column="DATA_DT", verbose_name="数据日期")
    genr_acct_id = models.CharField(db_column="GENR_ACCT_ID", max_length=60, verbose_name="通用账户号")
    orig_acct_id = models.CharField(db_column="ORIG_ACCT_ID", max_length=60, null=True, blank=True, verbose_name="原始账号")
    relat_acct_id = models.CharField(db_column="RELAT_ACCT_ID", max_length=60, null=True, blank=True)
    acct_name = models.CharField(db_column="ACCT_NAME", max_length=60, null=True, blank=True)
    src_sys_id = models.CharField(db_column="SRC_SYS_ID", max_length=60, null=True, blank=True)
    biz_type_cd = models.CharField(db_column="BIZ_TYPE_CD", max_length=10, null=True, blank=True)
    acct_class_cd = models.CharField(db_column="ACCT_CLASS_CD", max_length=1, null=True, blank=True)
    acct_stat_cd = models.CharField(db_column="ACCT_STAT_CD", max_length=2, null=True, blank=True)
    corp_id = models.CharField(db_column="CORP_ID", max_length=60, null=True, blank=True)
    mng_org_id = models.CharField(db_column="MNG_ORG_ID", max_length=12, null=True, blank=True)
    accnt_org_id = models.CharField(db_column="ACCNT_ORG_ID", max_length=8, null=True, blank=True)
    check_org_id = models.CharField(db_column="CHECK_ORG_ID", max_length=14, null=True, blank=True)
    org_lev_cd = models.CharField(db_column="ORG_LEV_CD", max_length=2, null=True, blank=True)
    org_belong_area_cd = models.CharField(db_column="ORG_BELONG_AREA_CD", max_length=6, null=True, blank=True)
    acct_belong_branch_id = models.CharField(db_column="ACCT_BELONG_BRANCH_ID", max_length=14, null=True, blank=True)
    uplev_mngaccnt_prod_id = models.CharField(db_column="UPLEV_MNGACCNT_PROD_ID", max_length=20, null=True, blank=True)
    mng_accnt_prod_id = models.CharField(db_column="MNG_ACCNT_PROD_ID", max_length=20, null=True, blank=True)
    biz_prod_id = models.CharField(db_column="BIZ_PROD_ID", max_length=20, null=True, blank=True)
    mng_dept_id = models.CharField(db_column="MNG_DEPT_ID", max_length=12, null=True, blank=True)
    biz_dept_id = models.CharField(db_column="BIZ_DEPT_ID", max_length=14, null=True, blank=True)
    line_id = models.CharField(db_column="LINE_ID", max_length=60, null=True, blank=True)
    channel_id = models.CharField(db_column="CHANNEL_ID", max_length=60, null=True, blank=True)
    cust_id = models.CharField(db_column="CUST_ID", max_length=32, null=True, blank=True)
    ecif_cust_id = models.CharField(db_column="ECIF_CUST_ID", max_length=10, null=True, blank=True)
    cust_type_cd = models.CharField(db_column="CUST_TYPE_CD", max_length=9, null=True, blank=True)
    cust_belong_indus_cd = models.CharField(db_column="CUST_BELONG_INDUS_CD", max_length=5, null=True, blank=True)
    gb_corp_scale_cd = models.CharField(db_column="GB_CORP_SCALE_CD", max_length=1, null=True, blank=True)
    cust_crdt_lev = models.CharField(db_column="CUST_CRDT_LEV", max_length=3, null=True, blank=True)
    cust_val_layer_type_cd = models.CharField(db_column="CUST_VAL_LAYER_TYPE_CD", max_length=6, null=True, blank=True)
    cust_star_id = models.CharField(db_column="CUST_STAR_ID", max_length=10, null=True, blank=True)
    small_cust_flg = models.CharField(db_column="SMALL_CUST_FLG", max_length=1, null=True, blank=True)
    tech_inno_fin_cust_flg = models.CharField(db_column="TECH_INNO_FIN_CUST_FLG", max_length=1, null=True, blank=True)
    supply_chain_core_cust_flg = models.CharField(db_column="SUPPLY_CHAIN_CORE_CUST_FLG", max_length=1, null=True, blank=True)
    online_flg = models.CharField(db_column="ONLINE_FLG", max_length=1, null=True, blank=True)
    green_loan_flg = models.CharField(db_column="GREEN_LOAN_FLG", max_length=1, null=True, blank=True)
    stra_emerge_indus_flg = models.CharField(db_column="STRA_EMERGE_INDUS_FLG", max_length=1, null=True, blank=True)
    srdi_flg = models.CharField(db_column="SRDI_FLG", max_length=1, null=True, blank=True)
    inclsv_farmer_loan_flg = models.CharField(db_column="INCLSV_FARMER_LOAN_FLG", max_length=1, null=True, blank=True)
    farmer_loan_flg = models.CharField(db_column="FARMER_LOAN_FLG", max_length=1, null=True, blank=True)
    rural_rvtlzn_flg = models.CharField(db_column="RURAL_RVTLZN_FLG", max_length=1, null=True, blank=True)
    incr_loan_flg = models.CharField(db_column="INCR_LOAN_FLG", max_length=1, null=True, blank=True)
    manuf_indus_loan_flg = models.CharField(db_column="MANUF_INDUS_LOAN_FLG", max_length=1, null=True, blank=True)
    ppp_loan_flg = models.CharField(db_column="PPP_LOAN_FLG", max_length=1, null=True, blank=True)
    star_stra_cust_loan_flg = models.CharField(db_column="STAR_STRA_CUST_LOAN_FLG", max_length=1, null=True, blank=True)
    imp_proj_loan_flg = models.CharField(db_column="IMP_PROJ_LOAN_FLG", max_length=1, null=True, blank=True)
    lead_celoan_flg = models.CharField(db_column="LEAD_CELOAN_FLG", max_length=1, null=True, blank=True)
    indiv_first_house_loan_flg = models.CharField(db_column="INDIV_FIRST_HOUSE_LOAN_FLG", max_length=1, null=True, blank=True)
    indiv_nonfirsthouse_loan_flg = models.CharField(db_column="INDIV_NONFIRSTHOUSE_LOAN_FLG", max_length=1, null=True, blank=True)
    overfiveyear_nonhouseloan_flg = models.CharField(db_column="OVERFIVEYEAR_NONHOUSELOAN_FLG", max_length=1, null=True, blank=True)
    city_upd_loan_flg = models.CharField(db_column="CITY_UPD_LOAN_FLG", max_length=1, null=True, blank=True)
    other_rmb_loan_flg = models.CharField(db_column="OTHER_RMB_LOAN_FLG", max_length=1, null=True, blank=True)
    manuf_indus_longterm_loan_flg = models.CharField(db_column="MANUF_INDUS_LONGTERM_LOAN_FLG", max_length=1, null=True, blank=True)
    tech_inno_loan_flg = models.CharField(db_column="TECH_INNO_LOAN_FLG", max_length=1, null=True, blank=True)
    priv_loan_flg = models.CharField(db_column="PRIV_LOAN_FLG", max_length=1, null=True, blank=True)
    midsmallmicro_corp_midlqdyln_flg = models.CharField(db_column="MIDSMALLMICRO_CORP_MIDLQDYLN_FLG", max_length=1, null=True, blank=True)
    smallmicrocorp_non_repaycap_renewln_flg = models.CharField(db_column="SMALLMICROCORP_NON_REPAYCAP_RENEWLN_FLG", max_length=1, null=True, blank=True)
    hs_bank_epay_flg = models.CharField(db_column="HS_BANK_EPAY_FLG", max_length=1, null=True, blank=True)
    spec_bond_flg = models.CharField(db_column="SPEC_BOND_FLG", max_length=1, null=True, blank=True)
    invest_indus_type_cd = models.CharField(db_column="INVEST_INDUS_TYPE_CD", max_length=5, null=True, blank=True)
    card_type_cd = models.CharField(db_column="CARD_TYPE_CD", max_length=20, null=True, blank=True)
    asset_cat_cd = models.CharField(db_column="ASSET_CAT_CD", max_length=20, null=True, blank=True)
    asset_three_cat_cd = models.CharField(db_column="ASSET_THREE_CAT_CD", max_length=10, null=True, blank=True)
    txn_countpty_id = models.CharField(db_column="TXN_COUNTPTY_ID", max_length=60, null=True, blank=True)
    txn_countpty_type_cd = models.CharField(db_column="TXN_COUNTPTY_TYPE_CD", max_length=9, null=True, blank=True)
    int_st_dt = models.DateField(db_column="INT_ST_DT", null=True, blank=True)
    mature_dt = models.DateField(db_column="MATURE_DT", null=True, blank=True)
    orig_mature_dt = models.DateField(db_column="ORIG_MATURE_DT", null=True, blank=True)
    stl_dt = models.DateField(db_column="STL_DT", null=True, blank=True)
    verif_dt = models.DateField(db_column="VERIF_DT", null=True, blank=True)
    txn_dt = models.DateField(db_column="TXN_DT", null=True, blank=True)
    issue_dt = models.DateField(db_column="ISSUE_DT", null=True, blank=True)
    acct_term = models.CharField(db_column="ACCT_TERM", max_length=60, null=True, blank=True)
    term_unit = models.CharField(db_column="TERM_UNIT", max_length=60, null=True, blank=True)
    overdue_day_cnt = models.IntegerField(db_column="OVERDUE_DAY_CNT", null=True, blank=True)
    exec_rate = models.DecimalField(db_column="EXEC_RATE", max_digits=12, decimal_places=8, null=True, blank=True)
    fact_rate = models.DecimalField(db_column="FACT_RATE", max_digits=12, decimal_places=8, null=True, blank=True)
    rate_adjust_mode_cd = models.CharField(db_column="RATE_ADJUST_MODE_CD", max_length=2, null=True, blank=True)
    rate_float_mode_cd = models.CharField(db_column="RATE_FLOAT_MODE_CD", max_length=1, null=True, blank=True)
    cal_int_base_cd = models.CharField(db_column="CAL_INT_BASE_CD", max_length=10, null=True, blank=True)
    fix_cur_flg = models.CharField(db_column="FIX_CUR_FLG", max_length=1, null=True, blank=True)
    bad_loan_flg = models.CharField(db_column="BAD_LOAN_FLG", max_length=1, null=True, blank=True)
    make_int_asset_flg = models.CharField(db_column="MAKE_INT_ASSET_FLG", max_length=1, null=True, blank=True)
    cal_int_libility_flg = models.CharField(db_column="CAL_INT_LIBILITY_FLG", max_length=1, null=True, blank=True)
    overdue_flg = models.CharField(db_column="OVERDUE_FLG", max_length=1, null=True, blank=True)
    asset_sec_flg = models.CharField(db_column="ASSET_SEC_FLG", max_length=1, null=True, blank=True)
    repay_mode_cd = models.CharField(db_column="REPAY_MODE_CD", max_length=3, null=True, blank=True)
    main_guar_mode = models.CharField(db_column="MAIN_GUAR_MODE", max_length=7, null=True, blank=True)
    guar_mode_comb_cd = models.CharField(db_column="GUAR_MODE_COMB_CD", max_length=7, null=True, blank=True)
    five_lev_cat_cd = models.CharField(db_column="FIVE_LEV_CAT_CD", max_length=4, null=True, blank=True)
    captl_subj_id = models.CharField(db_column="CAPTL_SUBJ_ID", max_length=10, null=True, blank=True)
    ccy_cd = models.CharField(db_column="CCY_CD", max_length=3, null=True, blank=True)
    orig_amt = models.DecimalField(db_column="ORIG_AMT", max_digits=18, decimal_places=4, null=True, blank=True)
    cur_bal = models.DecimalField(db_column="CUR_BAL", max_digits=18, decimal_places=4, verbose_name="当前余额")
    bal_mon_accum = models.DecimalField(db_column="BAL_MON_ACCUM", max_digits=20, decimal_places=4, null=True, blank=True)
    bal_quar_accum = models.DecimalField(db_column="BAL_QUAR_ACCUM", max_digits=20, decimal_places=4, null=True, blank=True)
    bal_year_accum = models.DecimalField(db_column="BAL_YEAR_ACCUM", max_digits=20, decimal_places=4, null=True, blank=True)
    overdue_captl_amt = models.DecimalField(db_column="OVERDUE_CAPTL_AMT", max_digits=18, decimal_places=4, null=True, blank=True)
    bad_loan_amt = models.DecimalField(db_column="BAD_LOAN_AMT", max_digits=18, decimal_places=4, null=True, blank=True)
    int_adjust_subj_id = models.CharField(db_column="INT_ADJUST_SUBJ_ID", max_length=10, null=True, blank=True)
    int_adjust_amt = models.DecimalField(db_column="INT_ADJUST_AMT", max_digits=18, decimal_places=4, null=True, blank=True)
    int_adjust_bal_mon_accum = models.DecimalField(db_column="INT_ADJUST_BAL_MON_ACCUM", max_digits=20, decimal_places=4, null=True, blank=True)
    int_adjust_bal_quar_accum = models.DecimalField(db_column="INT_ADJUST_BAL_QUAR_ACCUM", max_digits=20, decimal_places=4, null=True, blank=True)
    int_adjust_bal_year_accum = models.DecimalField(db_column="INT_ADJUST_BAL_YEAR_ACCUM", max_digits=20, decimal_places=4, null=True, blank=True)
    int_income_subj_id = models.CharField(db_column="INT_INCOME_SUBJ_ID", max_length=10, null=True, blank=True)
    accrual_int_income = models.DecimalField(db_column="ACCRUAL_INT_INCOME", max_digits=18, decimal_places=4, null=True, blank=True)
    int_income = models.DecimalField(db_column="INT_INCOME", max_digits=18, decimal_places=4, null=True, blank=True)
    mon_int_income = models.DecimalField(db_column="MON_INT_INCOME", max_digits=18, decimal_places=4, null=True, blank=True)
    quar_int_income = models.DecimalField(db_column="QUAR_INT_INCOME", max_digits=20, decimal_places=4, null=True, blank=True)
    year_int_income = models.DecimalField(db_column="YEAR_INT_INCOME", max_digits=20, decimal_places=4, null=True, blank=True)
    int_exp_subj_id = models.CharField(db_column="INT_EXP_SUBJ_ID", max_length=10, null=True, blank=True)
    int_exp = models.DecimalField(db_column="INT_EXP", max_digits=18, decimal_places=4, null=True, blank=True)
    mon_int_exp = models.DecimalField(db_column="MON_INT_EXP", max_digits=20, decimal_places=4, null=True, blank=True)
    quar_int_exp = models.DecimalField(db_column="QUAR_INT_EXP", max_digits=20, decimal_places=4, null=True, blank=True)
    year_int_exp = models.DecimalField(db_column="YEAR_INT_EXP", max_digits=20, decimal_places=4, null=True, blank=True)
    accrue_int_subj_id = models.CharField(db_column="ACCRUE_INT_SUBJ_ID", max_length=10, null=True, blank=True)
    accrue_int = models.DecimalField(db_column="ACCRUE_INT", max_digits=18, decimal_places=4, null=True, blank=True)
    shldpay_int_subj_id = models.CharField(db_column="SHLDPAY_INT_SUBJ_ID", max_length=10, null=True, blank=True)
    shldpay_int_bal = models.DecimalField(db_column="SHLDPAY_INT_BAL", max_digits=18, decimal_places=4, null=True, blank=True)
    shldrecv_int_subj_id = models.CharField(db_column="SHLDRECV_INT_SUBJ_ID", max_length=10, null=True, blank=True)
    shldrecv_int_bal = models.DecimalField(db_column="SHLDRECV_INT_BAL", max_digits=18, decimal_places=4, null=True, blank=True)
    int_net_income = models.DecimalField(db_column="INT_NET_INCOME", max_digits=18, decimal_places=4, null=True, blank=True)
    int_net_income_mon_accum = models.DecimalField(db_column="INT_NET_INCOME_MON_ACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    int_net_income_quar_accum = models.DecimalField(db_column="INT_NET_INCOME_QUAR_ACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    int_net_income_year_accum = models.DecimalField(db_column="INT_NET_INCOME_YEAR_ACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    orig_ftp_rate = models.DecimalField(db_column="ORIG_FTP_RATE", max_digits=12, decimal_places=8, null=True, blank=True)
    endo_adjust_point_diff = models.DecimalField(db_column="ENDO_ADJUST_POINT_DIFF", max_digits=12, decimal_places=8, null=True, blank=True)
    ftp_sys_adjust_amt = models.DecimalField(db_column="FTP_SYS_ADJUST_AMT", max_digits=18, decimal_places=4, null=True, blank=True)
    subsidy_adjust_point_diff = models.DecimalField(db_column="SUBSIDY_ADJUST_POINT_DIFF", max_digits=12, decimal_places=8, null=True, blank=True)
    subsidy_adjust_rate = models.DecimalField(db_column="SUBSIDY_ADJUST_RATE", max_digits=12, decimal_places=8, null=True, blank=True)
    subsidy_adjust_amt = models.DecimalField(db_column="SUBSIDY_ADJUST_AMT", max_digits=18, decimal_places=4, null=True, blank=True)
    final_ftp_rate = models.DecimalField(db_column="FINAL_FTP_RATE", max_digits=12, decimal_places=8, null=True, blank=True)
    ftp_rate_diff = models.DecimalField(db_column="FTP_RATE_DIFF", max_digits=12, decimal_places=8, null=True, blank=True)
    orig_ftp_incexp_daccum = models.DecimalField(db_column="ORIG_FTP_INCEXP_DACCUM", max_digits=20, decimal_places=4, null=True, blank=True)
    orig_ftp_incexp_maccum = models.DecimalField(db_column="ORIG_FTP_INCEXP_MACCUM", max_digits=20, decimal_places=4, null=True, blank=True)
    orig_ftp_incexp_qaccum = models.DecimalField(db_column="ORIG_FTP_INCEXP_QACCUM", max_digits=20, decimal_places=4, null=True, blank=True)
    orig_ftp_incexp_yaccum = models.DecimalField(db_column="ORIG_FTP_INCEXP_YACCUM", max_digits=20, decimal_places=4, null=True, blank=True)
    final_ftp_incexp_daccum = models.DecimalField(db_column="FINAL_FTP_INCEXP_DACCUM", max_digits=20, decimal_places=4, null=True, blank=True)
    final_ftp_incexp_maccum = models.DecimalField(db_column="FINAL_FTP_INCEXP_MACCUM", max_digits=20, decimal_places=4, null=True, blank=True)
    final_ftp_incexp_qaccum = models.DecimalField(db_column="FINAL_FTP_INCEXP_QACCUM", max_digits=20, decimal_places=4, null=True, blank=True)
    final_ftp_incexp_yaccum = models.DecimalField(db_column="FINAL_FTP_INCEXP_YACCUM", max_digits=20, decimal_places=4, null=True, blank=True)
    aft_subsidy_ftp_incexp_daccum = models.DecimalField(db_column="AFT_SUBSIDY_FTP_INCEXP_DACCUM", max_digits=20, decimal_places=4, null=True, blank=True)
    aft_subsidy_ftp_incexp_maccum = models.DecimalField(db_column="AFT_SUBSIDY_FTP_INCEXP_MACCUM", max_digits=20, decimal_places=4, null=True, blank=True)
    aft_subsidy_ftp_incexp_qaccum = models.DecimalField(db_column="AFT_SUBSIDY_FTP_INCEXP_QACCUM", max_digits=20, decimal_places=4, null=True, blank=True)
    aft_subsidy_ftp_incexp_yaccum = models.DecimalField(db_column="AFT_SUBSIDY_FTP_INCEXP_YACCUM", max_digits=20, decimal_places=4, null=True, blank=True)
    ftp_net_income_day_accum = models.DecimalField(db_column="FTP_NET_INCOME_DAY_ACCUM", max_digits=20, decimal_places=4, null=True, blank=True)
    ftp_net_income_mon_accum = models.DecimalField(db_column="FTP_NET_INCOME_MON_ACCUM", max_digits=20, decimal_places=4, null=True, blank=True)
    ftp_net_income_quar_accum = models.DecimalField(db_column="FTP_NET_INCOME_QUAR_ACCUM", max_digits=20, decimal_places=4, null=True, blank=True)
    ftp_net_income_year_accum = models.DecimalField(db_column="FTP_NET_INCOME_YEAR_ACCUM", max_digits=20, decimal_places=4, null=True, blank=True)
    hand_fee_income_subj_id = models.CharField(db_column="HAND_FEE_INCOME_SUBJ_ID", max_length=10, null=True, blank=True)
    bef_prctaxsplt_handfeeinc = models.DecimalField(db_column="BEF_PRCTAXSPL_HANDFEEINC", max_digits=18, decimal_places=4, null=True, blank=True)
    aft_prctaxsplt_handfeeinc = models.DecimalField(db_column="AFT_PRCTAXSPL_HANDFEEINC", max_digits=18, decimal_places=4, null=True, blank=True)
    aft_prctaxsplt_handfeeinc_maccum = models.DecimalField(db_column="AFT_PRCTAXSPL_HANDFEEINC_MACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    aft_prctaxsplt_handfeeinc_qaccum = models.DecimalField(db_column="AFT_PRCTAXSPL_HANDFEEINC_QACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    aft_prctaxsplt_handfeeinc_yaccum = models.DecimalField(db_column="AFT_PRCTAXSPL_HANDFEEINC_YACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    headorg_aptn_handfeeinc = models.DecimalField(db_column="HEADORG_APTN_HANDFEEINC", max_digits=18, decimal_places=4, null=True, blank=True)
    branch_aptn_handfeeinc = models.DecimalField(db_column="BRANCH_APTN_HANDFEEINC", max_digits=18, decimal_places=4, null=True, blank=True)
    sub_branch_aptn_handfeeinc = models.DecimalField(db_column="SUB_BRANCH_APTN_HANDFEEINC", max_digits=18, decimal_places=4, null=True, blank=True)
    handfeeexp_subj_id = models.CharField(db_column="HANDFEEEXP_SUBJ_ID", max_length=10, null=True, blank=True)
    hand_fee_and_commiss_exp = models.DecimalField(db_column="HAND_FEE_AND_COMMISS_EXP", max_digits=18, decimal_places=4, null=True, blank=True)
    handfeeexp_maccum = models.DecimalField(db_column="HANDFEEEXP_MACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    handfeeexp_qaccum = models.DecimalField(db_column="HANDFEEEXP_QACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    handfeeexp_yaccum = models.DecimalField(db_column="HANDFEEEXP_YACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    headorg_aptn_handfeeexp = models.DecimalField(db_column="HEADORG_APTN_HANDFEEEXP", max_digits=18, decimal_places=4, null=True, blank=True)
    branch_aptn_handfeeexp = models.DecimalField(db_column="BRANCH_APTN_HANDFEEEXP", max_digits=18, decimal_places=4, null=True, blank=True)
    sub_branch_aptn_handfeeexp = models.DecimalField(db_column="SUB_BRANCH_APTN_HANDFEEEXP", max_digits=18, decimal_places=4, null=True, blank=True)
    handfee_net_income = models.DecimalField(db_column="HANDFEE_NET_INCOME", max_digits=18, decimal_places=4, null=True, blank=True)
    handfee_netinc_maccum = models.DecimalField(db_column="HANDFEE_NETINC_MACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    handfee_netinc_qaccum = models.DecimalField(db_column="HANDFEE_NETINC_QACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    handfee_netinc_yaccum = models.DecimalField(db_column="HANDFEE_NETINC_YACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    invest_pl_subj_id = models.CharField(db_column="INVEST_PL_SUBJ_ID", max_length=10, null=True, blank=True)
    invest_pl = models.DecimalField(db_column="INVEST_PL", max_digits=18, decimal_places=4, null=True, blank=True)
    after_prctaxsplt_invest_pl = models.DecimalField(db_column="AFTER_PRCTAXSPL_INVEST_PL", max_digits=18, decimal_places=4, null=True, blank=True)
    mon_invest_pl = models.DecimalField(db_column="MON_INVEST_PL", max_digits=20, decimal_places=4, null=True, blank=True)
    quar_invest_pl = models.DecimalField(db_column="QUAR_INVEST_PL", max_digits=20, decimal_places=4, null=True, blank=True)
    year_invest_pl = models.DecimalField(db_column="YEAR_INVEST_PL", max_digits=20, decimal_places=4, null=True, blank=True)
    fair_val_alter_subj_id = models.CharField(db_column="FAIR_VAL_ALTER_SUBJ_ID", max_length=10, null=True, blank=True)
    fair_val_alter = models.DecimalField(db_column="FAIR_VAL_ALTER", max_digits=18, decimal_places=4, null=True, blank=True)
    fair_val_alter_mon_accum = models.DecimalField(db_column="FAIR_VAL_ALTER_MON_ACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    fair_val_alter_quar_accum = models.DecimalField(db_column="FAIR_VAL_ALTER_QUAR_ACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    fair_val_alter_year_accum = models.DecimalField(db_column="FAIR_VAL_ALTER_YEAR_ACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    fairval_alter_pl_subj_id = models.CharField(db_column="FAIRVAL_ALTER_PL_SUBJ_ID", max_length=10, null=True, blank=True)
    fair_val_alter_pl = models.DecimalField(db_column="FAIR_VAL_ALTER_PL", max_digits=18, decimal_places=4, null=True, blank=True)
    mon_fair_val_alter_pl = models.DecimalField(db_column="MON_FAIR_VAL_ALTER_PL", max_digits=20, decimal_places=4, null=True, blank=True)
    quar_fair_val_alter_pl = models.DecimalField(db_column="QUAR_FAIR_VAL_ALTER_PL", max_digits=20, decimal_places=4, null=True, blank=True)
    year_fair_val_alter_pl = models.DecimalField(db_column="YEAR_FAIR_VAL_ALTER_PL", max_digits=20, decimal_places=4, null=True, blank=True)
    other_yield_subj_id = models.CharField(db_column="OTHER_YIELD_SUBJ_ID", max_length=10, null=True, blank=True)
    other_yield = models.DecimalField(db_column="OTHER_YIELD", max_digits=18, decimal_places=4, null=True, blank=True)
    other_yield_mon_accum = models.DecimalField(db_column="OTHER_YIELD_MON_ACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    other_yield_quar_accum = models.DecimalField(db_column="OTHER_YIELD_QUAR_ACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    other_yield_year_accum = models.DecimalField(db_column="OTHER_YIELD_YEAR_ACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    other_biz_income_subj_id = models.CharField(db_column="OTHER_BIZ_INCOME_SUBJ_ID", max_length=10, null=True, blank=True)
    other_biz_income = models.DecimalField(db_column="OTHER_BIZ_INCOME", max_digits=18, decimal_places=4, null=True, blank=True)
    other_biz_income_mon_accum = models.DecimalField(db_column="OTHER_BIZ_INCOME_MON_ACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    other_biz_income_quar_accum = models.DecimalField(db_column="OTHER_BIZ_INCOME_QUAR_ACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    other_biz_income_year_accum = models.DecimalField(db_column="OTHER_BIZ_INCOME_YEAR_ACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    asset_handle_pl_subj_id = models.CharField(db_column="ASSET_HANDLE_PL_SUBJ_ID", max_length=10, null=True, blank=True)
    asset_handle_pl = models.DecimalField(db_column="ASSET_HANDLE_PL", max_digits=18, decimal_places=4, null=True, blank=True)
    asset_handle_pl_mon_accum = models.DecimalField(db_column="ASSET_HANDLE_PL_MON_ACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    asset_handle_pl_quar_accum = models.DecimalField(db_column="ASSET_HANDLE_PL_QUAR_ACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    asset_handle_pl_year_accum = models.DecimalField(db_column="ASSET_HANDLE_PL_YEAR_ACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    exch_pl_subj_id = models.CharField(db_column="EXCH_PL_SUBJ_ID", max_length=10, null=True, blank=True)
    exch_pl = models.DecimalField(db_column="EXCH_PL", max_digits=18, decimal_places=4, null=True, blank=True)
    exch_pl_mon_accum = models.DecimalField(db_column="EXCH_PL_MON_ACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    exch_pl_quar_accum = models.DecimalField(db_column="EXCH_PL_QUAR_ACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    exch_pl_year_accum = models.DecimalField(db_column="EXCH_PL_YEAR_ACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    day_after_ftp_biz_income = models.DecimalField(db_column="DAY_AFTER_FTP_BIZ_INCOME", max_digits=20, decimal_places=4, null=True, blank=True)
    mon_after_ftp_biz_income = models.DecimalField(db_column="MON_AFTER_FTP_BIZ_INCOME", max_digits=20, decimal_places=4, null=True, blank=True)
    quar_after_ftp_biz_income = models.DecimalField(db_column="QUAR_AFTER_FTP_BIZ_INCOME", max_digits=20, decimal_places=4, null=True, blank=True)
    year_after_ftp_biz_income = models.DecimalField(db_column="YEAR_AFTER_FTP_BIZ_INCOME", max_digits=20, decimal_places=4, null=True, blank=True)
    tax_and_attach_subj_id = models.CharField(db_column="TAX_AND_ATTACH_SUBJ_ID", max_length=10, null=True, blank=True)
    tax_and_attach_amt = models.DecimalField(db_column="TAX_AND_ATTACH_AMT", max_digits=18, decimal_places=4, null=True, blank=True)
    tax_and_attach_amt_yaccum = models.DecimalField(db_column="TAX_AND_ATTACH_AMT_YACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    income_tax_subj_id = models.CharField(db_column="INCOME_TAX_SUBJ_ID", max_length=10, null=True, blank=True)
    income_tax_mon_accum = models.DecimalField(db_column="INCOME_TAX_MON_ACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    income_tax_year_accum = models.DecimalField(db_column="INCOME_TAX_YEAR_ACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    mngfee_subj_id = models.CharField(db_column="MNGFEE_SUBJ_ID", max_length=10, null=True, blank=True)
    biz_and_mng_fee = models.DecimalField(db_column="BIZ_AND_MNG_FEE", max_digits=28, decimal_places=14, null=True, blank=True)
    mngfee_yaccum = models.DecimalField(db_column="MNGFEE_YACCUM", max_digits=28, decimal_places=14, null=True, blank=True)
    mngfee_direct_fee = models.DecimalField(db_column="MNGFEE_DIRECT_FEE", max_digits=28, decimal_places=14, null=True, blank=True)
    mngfee_directfee_yaccum = models.DecimalField(db_column="MNGFEE_DIRECTFEE_YACCUM", max_digits=28, decimal_places=14, null=True, blank=True)
    mngfee_direct_inacctamt = models.DecimalField(db_column="MNGFEE_DIRECT_INACCTAMT", max_digits=28, decimal_places=14, null=True, blank=True)
    mngfee_direct_inacctamt_yaccum = models.DecimalField(db_column="MNGFEE_DIRECT_INACCTAMT_YACCUM", max_digits=28, decimal_places=14, null=True, blank=True)
    mngfee_headorg_directfee = models.DecimalField(db_column="MNGFEE_HEADORG_DIRECTFEE", max_digits=28, decimal_places=14, null=True, blank=True)
    mngfee_headorg_directfee_yaccum = models.DecimalField(db_column="MNGFEE_HEADORG_DIRECTFEE_YACCUM", max_digits=28, decimal_places=14, null=True, blank=True)
    mngfee_branch_directfee = models.DecimalField(db_column="MNGFEE_BRANCH_DIRECTFEE", max_digits=28, decimal_places=14, null=True, blank=True)
    mngfee_branch_directfee_yaccum = models.DecimalField(db_column="MNGFEE_BRANCH_DIRECTFEE_YACCUM", max_digits=28, decimal_places=14, null=True, blank=True)
    mngfee_indir_fee = models.DecimalField(db_column="MNGFEE_INDIR_FEE", max_digits=28, decimal_places=14, null=True, blank=True)
    mngfee_indirfee_yaccum = models.DecimalField(db_column="MNGFEE_INDIRFEE_YACCUM", max_digits=28, decimal_places=14, null=True, blank=True)
    mngfee_headorg_indirfee = models.DecimalField(db_column="MNGFEE_HEADORG_INDIRFEE", max_digits=28, decimal_places=14, null=True, blank=True)
    mngfee_headorg_indirfee_yaccum = models.DecimalField(db_column="MNGFEE_HEADORG_INDIRFEE_YACCUM", max_digits=28, decimal_places=14, null=True, blank=True)
    mngfee_branch_indirfee = models.DecimalField(db_column="MNGFEE_BRANCH_INDIRFEE", max_digits=28, decimal_places=14, null=True, blank=True)
    mngfee_branch_indirfee_yaccum = models.DecimalField(db_column="MNGFEE_BRANCH_INDIRFEE_YACCUM", max_digits=28, decimal_places=14, null=True, blank=True)
    impair_loss_subj_id = models.CharField(db_column="IMPAIR_LOSS_SUBJ_ID", max_length=10, null=True, blank=True)
    lev5_comn_asset_impair = models.DecimalField(db_column="LEV5_COMN_ASSET_IMPAIR", max_digits=18, decimal_places=4, null=True, blank=True)
    lev5_spec_asset_impair = models.DecimalField(db_column="LEV5_SPEC_ASSET_IMPAIR", max_digits=18, decimal_places=4, null=True, blank=True)
    i9_asset_impair = models.DecimalField(db_column="I9_ASSET_IMPAIR", max_digits=18, decimal_places=4, null=True, blank=True)
    verif_amt = models.DecimalField(db_column="VERIF_AMT", max_digits=18, decimal_places=4, null=True, blank=True)
    after_verif_back_captl_amt = models.DecimalField(db_column="AFTER_VERIF_BACK_CAPTL_AMT", max_digits=18, decimal_places=4, null=True, blank=True)
    i9_asset_impair_loss = models.DecimalField(db_column="I9_ASSET_IMPAIR_LOSS", max_digits=18, decimal_places=4, null=True, blank=True)
    i9_asset_impair_loss_yaccum = models.DecimalField(db_column="I9_ASSET_IMPAIR_LOSS_YACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    lev5_asset_impair_loss = models.DecimalField(db_column="LEV5_ASSET_IMPAIR_LOSS", max_digits=18, decimal_places=4, null=True, blank=True)
    lev5_asset_impair_loss_yaccum = models.DecimalField(db_column="LEV5_ASSET_IMPAIR_LOSS_YACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    other_biz_exp_subj_id = models.CharField(db_column="OTHER_BIZ_EXP_SUBJ_ID", max_length=10, null=True, blank=True)
    other_biz_exp = models.DecimalField(db_column="OTHER_BIZ_EXP", max_digits=18, decimal_places=4, null=True, blank=True)
    other_biz_exp_year_accum = models.DecimalField(db_column="OTHER_BIZ_EXP_YEAR_ACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    biz_exp = models.DecimalField(db_column="BIZ_EXP", max_digits=18, decimal_places=4, null=True, blank=True)
    biz_exp_year_accum = models.DecimalField(db_column="BIZ_EXP_YEAR_ACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    non_biz_incexp_subj_id = models.CharField(db_column="NON_BIZ_INCEXP_SUBJ_ID", max_length=10, null=True, blank=True)
    non_biz_income_expense = models.DecimalField(db_column="NON_BIZ_INCOME_EXPENSE", max_digits=18, decimal_places=4, null=True, blank=True)
    non_biz_incexp_yaccum = models.DecimalField(db_column="NON_BIZ_INCEXP_YACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    biz_ftp_profit = models.DecimalField(db_column="BIZ_FTP_PROFIT", max_digits=18, decimal_places=4, null=True, blank=True)
    biz_ftp_profit_year_accum = models.DecimalField(db_column="BIZ_FTP_PROFIT_YEAR_ACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    profit_tot_amt = models.DecimalField(db_column="PROFIT_TOT_AMT", max_digits=20, decimal_places=4, null=True, blank=True)
    profit_tot_amt_year_accum = models.DecimalField(db_column="PROFIT_TOT_AMT_YEAR_ACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    net_profit_mon_accum = models.DecimalField(db_column="NET_PROFIT_MON_ACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    net_profit_year_accum = models.DecimalField(db_column="NET_PROFIT_YEAR_ACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    before_pro_profit_tot_amt = models.DecimalField(db_column="BEFORE_PRO_PROFIT_TOT_AMT", max_digits=18, decimal_places=4, null=True, blank=True)
    bef_pro_tot_profit_yaccum = models.DecimalField(db_column="BEF_PRO_TOT_PROFIT_YACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    regul_crdt_rwa = models.DecimalField(db_column="REGUL_CRDT_RWA", max_digits=18, decimal_places=4, null=True, blank=True)
    crdt_risk_ecocap_adj_coeff = models.DecimalField(db_column="CRDT_RISK_ECOCAP_ADJ_COEFF", max_digits=12, decimal_places=8, null=True, blank=True)
    aftcoeff_crdt_risk_ecocap = models.DecimalField(db_column="AFTCOEFF_CRDT_RISK_ECOCAP", max_digits=18, decimal_places=4, null=True, blank=True)
    aftcoeff_crdtrisk_ecocap_yaccum = models.DecimalField(db_column="AFTCOEFF_CRDTRISK_ECOCAP_YACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    crdt_risk_econm_capt_rwa = models.DecimalField(db_column="CRDT_RISK_ECONM_CAPT_RWA", max_digits=18, decimal_places=4, null=True, blank=True)
    crdtrisk_ecocap_rwa_yaccum = models.DecimalField(db_column="CRDTRISK_ECOCAP_RWA_YACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    oper_risk_econm_capt = models.DecimalField(db_column="OPER_RISK_ECONM_CAPT", max_digits=18, decimal_places=4, null=True, blank=True)
    operrisk_ecocap_yaccum = models.DecimalField(db_column="OPERRISK_ECOCAP_YACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    mkt_risk_econm_capt = models.DecimalField(db_column="MKT_RISK_ECONM_CAPT", max_digits=18, decimal_places=4, null=True, blank=True)
    mktrisk_ecocap_yaccum = models.DecimalField(db_column="MKTRISK_ECOCAP_YACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    econm_capt = models.DecimalField(db_column="ECONM_CAPT", max_digits=18, decimal_places=4, null=True, blank=True)
    econm_capt_year_accum = models.DecimalField(db_column="ECONM_CAPT_YEAR_ACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    regul_capt = models.DecimalField(db_column="REGUL_CAPT", max_digits=18, decimal_places=4, null=True, blank=True)
    regul_capt_year_accum = models.DecimalField(db_column="REGUL_CAPT_YEAR_ACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    crdt_risk_econm_capt_cost = models.DecimalField(db_column="CRDT_RISK_ECONM_CAPT_COST", max_digits=18, decimal_places=4, null=True, blank=True)
    crdt_risk_ecocap_cost_yaccum = models.DecimalField(db_column="CRDT_RISK_ECOCAP_COST_YACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    mkt_risk_econm_capt_cost = models.DecimalField(db_column="MKT_RISK_ECONM_CAPT_COST", max_digits=18, decimal_places=4, null=True, blank=True)
    mkt_risk_ecocap_cost_yaccum = models.DecimalField(db_column="MKT_RISK_ECOCAP_COST_YACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    oper_risk_econm_capt_cost = models.DecimalField(db_column="OPER_RISK_ECONM_CAPT_COST", max_digits=18, decimal_places=4, null=True, blank=True)
    oper_risk_ecocap_cost_yaccum = models.DecimalField(db_column="OPER_RISK_ECOCAP_COST_YACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    econm_capt_cost = models.DecimalField(db_column="ECONM_CAPT_COST", max_digits=18, decimal_places=4, null=True, blank=True)
    econm_capt_cost_year_accum = models.DecimalField(db_column="ECONM_CAPT_COST_YEAR_ACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    eva = models.DecimalField(db_column="EVA", max_digits=18, decimal_places=4, null=True, blank=True)
    eva_year_accum = models.DecimalField(db_column="EVA_YEAR_ACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    raroc = models.DecimalField(db_column="RAROC", max_digits=18, decimal_places=4, null=True, blank=True)
    raroc_year_accum = models.DecimalField(db_column="RAROC_YEAR_ACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    non_int_income = models.DecimalField(db_column="NON_INT_INCOME", max_digits=18, decimal_places=4, null=True, blank=True)
    non_int_income_mon_accum = models.DecimalField(db_column="NON_INT_INCOME_MON_ACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    non_int_income_quar_accum = models.DecimalField(db_column="NON_INT_INCOME_QUAR_ACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    non_int_income_year_accum = models.DecimalField(db_column="NON_INT_INCOME_YEAR_ACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    non_int_exp = models.DecimalField(db_column="NON_INT_EXP", max_digits=18, decimal_places=4, null=True, blank=True)
    non_int_exp_mon_accum = models.DecimalField(db_column="NON_INT_EXP_MON_ACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    non_int_exp_quar_accum = models.DecimalField(db_column="NON_INT_EXP_QUAR_ACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    non_int_exp_year_accum = models.DecimalField(db_column="NON_INT_EXP_YEAR_ACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    non_int_net_income = models.DecimalField(db_column="NON_INT_NET_INCOME", max_digits=18, decimal_places=4, null=True, blank=True)
    nonint_netincome_maccum = models.DecimalField(db_column="NONINT_NETINCOME_MACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    nonint_netincome_qaccum = models.DecimalField(db_column="NONINT_NETINCOME_QACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    nonint_netincome_yaccum = models.DecimalField(db_column="NONINT_NETINCOME_YACCUM", max_digits=18, decimal_places=4, null=True, blank=True)
    basis_cd = models.CharField(db_column="BASIS_CD", max_length=20, null=True, blank=True)
    cust_name = models.CharField(db_column="CUST_NAME", max_length=450, null=True, blank=True, verbose_name="客户名称")

    class Meta:
        abstract = True
        managed = False


class AcctSumDHistory(BaseAcctSum):
    """日汇总历史表"""

    class Meta:
        db_table = "i01_sz_acct_sum_d_history"
        managed = False
        verbose_name = "日汇总历史表"
        verbose_name_plural = "日汇总历史表"


class AcctSumMHistory(BaseAcctSum):
    """月汇总历史表"""

    class Meta:
        db_table = "i01_sz_acct_sum_m_history"
        managed = False
        verbose_name = "月汇总历史表"
        verbose_name_plural = "月汇总历史表"


class AcctSumD(BaseAcctSum):
    """日汇总表"""

    class Meta:
        db_table = "i01_sz_acct_sum_d"
        managed = False
        verbose_name = "日汇总表"
        verbose_name_plural = "日汇总表"


class LineId(models.Model):
    """条线编号表"""
    id = models.BigAutoField(primary_key=True, db_column="ID", verbose_name="自增ID")
    line_id = models.CharField(
        db_column="LINE_ID",
        max_length=60,
        null=True,
        blank=True,
        verbose_name="条线编号",
    )
    line_id_name = models.CharField(
        db_column="LINE_ID_NAME",
        max_length=300,
        null=True,
        blank=True,
        verbose_name="条线名称",
    )
    org_code = models.CharField(
        db_column="org_code",
        max_length=32,
        null=True,
        blank=True,
        verbose_name="管理部室",
    )

    class Meta:
        managed = False
        db_table = "line_id"
        verbose_name = "条线编号表"
        verbose_name_plural = "条线编号表"


class MngAccntProd(models.Model):
    """管会产品编号对应表"""
    id = models.BigAutoField(primary_key=True, db_column="ID", verbose_name="自增ID")
    mng_accnt_prod_id = models.CharField(
        db_column="MNG_ACCNT_PROD_ID",
        max_length=20,
        null=True,
        blank=True,
        verbose_name="五级产品编码",
    )
    mng_accnt_prod_name = models.CharField(
        db_column="MNG_ACCNT_PROD_NAME",
        max_length=300,
        null=True,
        blank=True,
        verbose_name="五级产品名称",
    )

    class Meta:
        managed = False
        db_table = "mng_accnt_prod"
        verbose_name = "管会产品编号对应表"
        verbose_name_plural = "管会产品编号对应表"
