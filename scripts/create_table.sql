CREATE TABLE `shenzhen_sys_user` (
    `id` bigint NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `employee_no` varchar(32) NOT NULL COMMENT '员工编号',
    `password` varchar(128) NOT NULL COMMENT '登录密码(加密保存)',
    `last_login_time` datetime DEFAULT NULL COMMENT '最后登录时间',
    `is_active` tinyint(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
    `employee_name` varchar(50) NOT NULL COMMENT '员工姓名',
    `user_status` char(2) NOT NULL DEFAULT '01' COMMENT '用户状态: 01正常 05暂停 09离职',
    `user_level` char(2) NOT NULL DEFAULT '00' COMMENT '用户级别: 99管理员 00普通用户',
    `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    `last_login_ip` varchar(45) DEFAULT NULL COMMENT '最后登录IP',
    `bind_ip` varchar(45) DEFAULT NULL COMMENT '绑定IP',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_employee_no` (`employee_no`),
    UNIQUE KEY `uk_sys_user_bind_ip` (`bind_ip`)
) ENGINE=InnoDB 
DEFAULT CHARSET=utf8mb4 
COLLATE=utf8mb4_general_ci 
COMMENT='系统用户表';


CREATE TABLE `shenzhen_org_unit` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `org_code` VARCHAR(32) NOT NULL COMMENT '机构编码',
    `credit_org_code` VARCHAR(32) DEFAULT NULL COMMENT '贷系统机构编码',
    `virtual_employee_no` VARCHAR(32) DEFAULT NULL COMMENT '公共虚拟员工号',
    `org_name` VARCHAR(100) NOT NULL COMMENT '机构名称',
    `org_type` CHAR(2) NOT NULL COMMENT '机构类型：00-分行，01-部室，02-支行，03-团队',
    `is_assessment_dept` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否考核部门：0-否，1-是',
    `leader_employee_no` VARCHAR(32) DEFAULT NULL COMMENT '主管领导员工号',
    `manager_employee_no` VARCHAR(32) DEFAULT NULL COMMENT '单位负责人员工号',
    `display_order` INT NOT NULL DEFAULT 0 COMMENT '排序号',
    `status` CHAR(2) NOT NULL DEFAULT '01' COMMENT '机构状态：01-正常，05-停用，09-取消',
    `parent_id` BIGINT DEFAULT NULL COMMENT '父机构ID',
    `remark` VARCHAR(255) DEFAULT NULL COMMENT '备注',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_org_unit_org_code` (`org_code`),
    KEY `idx_org_unit_parent_id` (`parent_id`),
    KEY `idx_org_unit_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='机构表';


CREATE TABLE `shenzhen_user_org_rel` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `user_id` BIGINT NOT NULL COMMENT '用户ID',
    `org_id` BIGINT NOT NULL COMMENT '机构ID',
    `credit_employee_no` VARCHAR(32) DEFAULT NULL COMMENT '贷系统员工编号',
    `team_member_no` VARCHAR(32) DEFAULT NULL COMMENT '团队成员编号',
    `team_org_code` VARCHAR(32) DEFAULT NULL COMMENT '团队机构编码',
    `line_code` VARCHAR(32) DEFAULT NULL COMMENT '所属条线编码',
    `employee_level` CHAR(2) DEFAULT NULL COMMENT '员工级别编码：00-分行领导，10-部室领导，13-部室主管，15-部室员工，20-支行领导，23-支行主管，25-支行员工',
    `is_customer_manager` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否客户经理：0-否，1-是',
    `position_name` VARCHAR(64) DEFAULT NULL COMMENT '岗位名称',
    `is_primary` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否主归属：0-否，1-是',
    `status` CHAR(2) NOT NULL DEFAULT '01' COMMENT '状态：01-有效，09-失效',
    `start_date` DATE DEFAULT NULL COMMENT '生效日期',
    `end_date` DATE DEFAULT NULL COMMENT '失效日期',
    `team_name` VARCHAR(64) NULL DEFAULT NULL COMMENT '团队名称',
    `remark` VARCHAR(255) DEFAULT NULL COMMENT '备注',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_org_rel_user_org` (`user_id`, `org_id`),
    KEY `idx_user_org_rel_user_id` (`user_id`),
    KEY `idx_user_org_rel_org_id` (`org_id`),
    KEY `idx_user_org_rel_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户机构关系表';


CREATE TABLE `perf_indicator` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `indicator_code` VARCHAR(64) NOT NULL COMMENT '指标编码，系统内唯一',
    `indicator_name` VARCHAR(128) NOT NULL COMMENT '指标名称',
    `parent_id` BIGINT DEFAULT NULL COMMENT '父指标ID，支持指标层级',
    `assessment_indicator_id` VARCHAR(64) DEFAULT NULL COMMENT '业绩考核指标ID，对应甲方考核配置表的指标ID',
    `category_code` VARCHAR(32) DEFAULT NULL COMMENT '指标分类编码，如 440/380',
    `category_name` VARCHAR(64) DEFAULT NULL COMMENT '指标分类名称，如 发展转型类/社会责任类',
    `line_code` VARCHAR(64) DEFAULT NULL COMMENT '指标条线编码',
    `indicator_standard` CHAR(2) DEFAULT '01' COMMENT '指标标准：01-时点，02-增量，03-日均，04-年累计',
    `display_unit` VARCHAR(32) DEFAULT NULL COMMENT '显示单位，如 元/万元/亿元/%',
    `decimal_places` TINYINT DEFAULT 2 COMMENT '小数位数',
    `display_type` VARCHAR(32) DEFAULT 'card' COMMENT '默认展示类型：card/trend/rank/table',
    `display_scope` VARCHAR(32) DEFAULT 'all' COMMENT '展示范围：all/card/trend/rank',
    `show_in_card` TINYINT NOT NULL DEFAULT 0 COMMENT '是否展示在顶部卡片：1是0否',
    `show_in_trend` TINYINT NOT NULL DEFAULT 0 COMMENT '是否展示在趋势图下拉：1是0否',
    `show_in_rank` TINYINT NOT NULL DEFAULT 0 COMMENT '是否展示在排名下拉：1是0否',
    `sort_no` INT NOT NULL DEFAULT 0 COMMENT '排序，值越小越靠前',
    `status` CHAR(2) NOT NULL DEFAULT '01' COMMENT '状态：01-启用，05-停用',
    `description` VARCHAR(1000) DEFAULT NULL COMMENT '指标描述',
    `remark` VARCHAR(1000) DEFAULT NULL COMMENT '备注',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_indicator_code` (`indicator_code`),
    KEY `idx_parent_id` (`parent_id`),
    KEY `idx_category_code` (`category_code`),
    KEY `idx_status_sort` (`status`, `sort_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='业绩看板-指标定义表';


CREATE TABLE `perf_indicator_rule` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `indicator_id` BIGINT NOT NULL COMMENT '指标ID',
    `rule_version` INT NOT NULL DEFAULT 1 COMMENT '规则版本号',
    `is_current` TINYINT NOT NULL DEFAULT 1 COMMENT '是否当前生效版本：1是0否',
    `rule_name` VARCHAR(128) DEFAULT NULL COMMENT '规则名称',
    `sql_template` LONGTEXT NOT NULL COMMENT '指标计算SQL模板',
    `target_sql_template` LONGTEXT DEFAULT NULL COMMENT '目标值SQL模板，可为空；用于完成率/目标值展示',
    `calc_mode` VARCHAR(32) NOT NULL DEFAULT 'single_value' COMMENT '计算模式：single_value/org_value/multi_value',
    `result_fields` VARCHAR(255) NOT NULL DEFAULT 'org_id,metric_value' COMMENT 'SQL输出字段定义，默认 org_id,metric_value',
    `org_prefix` VARCHAR(64) DEFAULT NULL COMMENT '输出机构编码前缀',
    `need_org_filter` TINYINT NOT NULL DEFAULT 1 COMMENT '是否需要按机构过滤：1是0否',
    `need_date_param` TINYINT NOT NULL DEFAULT 1 COMMENT '是否需要日期参数：1是0否',
    `need_day_count_param` TINYINT NOT NULL DEFAULT 0 COMMENT '是否需要天数参数：1是0否',
    `run_mode` VARCHAR(32) NOT NULL DEFAULT 'all_org' COMMENT '执行模式：all_org/single_org/both',
    `data_source_desc` VARCHAR(255) DEFAULT NULL COMMENT '数据来源说明，如 i01_sz_acct_sum_d',
    `display_value_field` VARCHAR(64) NOT NULL DEFAULT 'metric_value' COMMENT '默认展示值字段',
    `compare_value_field` VARCHAR(64) DEFAULT NULL COMMENT '用于辅助比较或展示的值字段，如 metric_value_2',
    `status` CHAR(2) NOT NULL DEFAULT '01' COMMENT '状态：01-启用，05-停用',
    `remark` VARCHAR(1000) DEFAULT NULL COMMENT '备注',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_indicator_version` (`indicator_id`, `rule_version`),
    KEY `idx_indicator_current` (`indicator_id`, `is_current`),
    KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='业绩看板-指标规则表';


CREATE TABLE `perf_indicator_result` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `data_dt` DATE NOT NULL COMMENT '数据日期',
    `indicator_id` BIGINT NOT NULL COMMENT '指标ID',
    `org_id` VARCHAR(64) NOT NULL COMMENT '机构ID，关联现有机构表',
    `metric_value` DECIMAL(20,4) DEFAULT NULL COMMENT '主指标值，前端默认展示值',
    `metric_value_2` DECIMAL(20,4) DEFAULT NULL COMMENT '辅助指标值2，如时点余额/日均值',
    `metric_value_3` DECIMAL(20,4) DEFAULT NULL COMMENT '辅助指标值3',
    `target_value` DECIMAL(20,4) DEFAULT NULL COMMENT '目标值',
    `completion_rate` DECIMAL(10,4) DEFAULT NULL COMMENT '完成率，如 1.0500 表示 105%',
    `rank_no` INT DEFAULT NULL COMMENT '当日该指标在当前层级下的排名',
    `is_topn` TINYINT NOT NULL DEFAULT 0 COMMENT '是否进入排名展示：1是0否',
    `calc_status` CHAR(2) NOT NULL DEFAULT '01' COMMENT '计算状态：01-成功，02-失败',
    `error_msg` VARCHAR(1000) DEFAULT NULL COMMENT '计算失败原因',
    `extra_json` JSON DEFAULT NULL COMMENT '扩展字段，存其他结果数据',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_dt_indicator_org` (`data_dt`, `indicator_id`, `org_id`),
    KEY `idx_indicator_dt` (`indicator_id`, `data_dt`),
    KEY `idx_org_indicator_dt` (`org_id`, `indicator_id`, `data_dt`),
    KEY `idx_dt_rank` (`data_dt`, `indicator_id`, `rank_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='业绩看板-指标结果表';


CREATE TABLE `data_import_log` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `file_name` VARCHAR(255) NOT NULL COMMENT '总行下发文件名',
    `data_date` DATE NOT NULL COMMENT '数据日期',
    `status` TINYINT NOT NULL DEFAULT 0 COMMENT '状态：0待处理 1成功 2失败 3执行中',
    `run_count` INT UNSIGNED NOT NULL DEFAULT 0 COMMENT '运行次数',
    `message` VARCHAR(1000) DEFAULT NULL COMMENT '状态说明',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_import_dt_file` (`data_date`, `file_name`),
    KEY `idx_import_dt_file` (`data_date`, `file_name`),
    KEY `idx_import_dt_status` (`data_date`, `status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='总行下发文件导入日志表';


CREATE TABLE `result_import_dependency` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `table_name` VARCHAR(128) NOT NULL COMMENT '结果表导入依赖的总行表名',
    `remark` VARCHAR(255) DEFAULT NULL COMMENT '备注',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_result_dep_table` (`table_name`),
    KEY `idx_result_dep_table` (`table_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='结果表导入依赖表配置';


CREATE TABLE `result_import_log` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `data_date` DATE NOT NULL COMMENT '数据日期',
    `status` TINYINT NOT NULL DEFAULT 0 COMMENT '状态：0待处理 1成功 2失败 3执行中',
    `message` VARCHAR(1000) DEFAULT NULL COMMENT '状态说明',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_result_import_dt` (`data_date`),
    KEY `idx_result_import_dt_status` (`data_date`, `status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='结果表导入任务日志表';


CREATE TABLE `result_import_indicator_log_post_profit` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `data_date` DATE NOT NULL COMMENT '任务日期',
    `indicator_id` BIGINT NOT NULL COMMENT '指标ID',
    `rule_id` BIGINT DEFAULT NULL COMMENT '规则ID',
    `status` TINYINT NOT NULL DEFAULT 0 COMMENT '状态：0待处理 1成功 2失败 3执行中',
    `message` VARCHAR(1000) DEFAULT NULL COMMENT '状态说明',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_pp_indicator_import_dt_indicator` (`data_date`, `indicator_id`),
    KEY `idx_pp_ind_imp_dt_st` (`data_date`, `status`),
    KEY `idx_pp_ind_imp_dt_ind` (`data_date`, `indicator_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='分润后结果表导入指标日志表';


CREATE TABLE `wf_process_def` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `process_code` VARCHAR(50) NOT NULL COMMENT '流程编码',
    `process_name` VARCHAR(100) NOT NULL COMMENT '流程名称',
    `business_type` VARCHAR(50) NOT NULL COMMENT '业务类型',
    `version` INT NOT NULL COMMENT '版本号',
    `status` VARCHAR(20) NOT NULL DEFAULT 'draft' COMMENT '状态：draft草稿/active启用/inactive停用',
    `is_latest` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否最新版本',
    `remark` VARCHAR(500) DEFAULT NULL COMMENT '备注',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_wf_proc_code_version` (`process_code`, `version`),
    KEY `idx_wf_proc_business` (`business_type`),
    KEY `idx_wf_proc_status` (`status`),
    KEY `idx_wf_proc_is_latest` (`is_latest`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='流程定义表';


CREATE TABLE `wf_node_def` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `process_def_id` BIGINT NOT NULL COMMENT '流程定义ID',
    `node_code` VARCHAR(50) NOT NULL COMMENT '节点编码',
    `node_name` VARCHAR(100) NOT NULL COMMENT '节点名称',
    `node_type` VARCHAR(30) NOT NULL COMMENT '节点类型：start开始节点/manual人工审核节点/auto自动处理节点/end结束节点',
    `auto_func_name` VARCHAR(100) DEFAULT NULL COMMENT '自动节点执行函数名',
    `node_order` INT DEFAULT NULL COMMENT '节点顺序',
    `is_parallel` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否并行节点',
    `parallel_mode` VARCHAR(30) DEFAULT NULL COMMENT '并行模式',
    `join_strategy` VARCHAR(30) DEFAULT NULL COMMENT '汇聚策略：all_pass全部通过/any_pass任意通过/custom自定义',
    `can_reject` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否允许驳回',
    `can_return` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否允许退回',
    `auto_create_task` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否自动创建任务',
    `remark` VARCHAR(500) DEFAULT NULL COMMENT '备注',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_wf_node_proc_node` (`process_def_id`, `node_code`),
    KEY `idx_wf_node_code` (`node_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='节点定义表';


CREATE TABLE `wf_node_assignee_rule` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `process_def_id` BIGINT NOT NULL COMMENT '流程定义ID',
    `node_code` VARCHAR(50) NOT NULL COMMENT '节点编码',
    `rule_type` VARCHAR(30) NOT NULL COMMENT '规则类型：applicant发起人/employee_level按员工级别/role按角色/fixed_user固定用户/org_leader机构负责人/custom自定义规则',
    `rule_value` VARCHAR(200) DEFAULT NULL COMMENT '规则值（如员工级别编码/角色编码/用户ID等）',
    `remark` VARCHAR(500) DEFAULT NULL COMMENT '备注',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_wf_rule_proc_node` (`process_def_id`, `node_code`),
    KEY `idx_wf_rule_type` (`rule_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='节点审批人规则表';


CREATE TABLE `wf_transition_def` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `process_def_id` BIGINT NOT NULL COMMENT '流程定义ID',
    `from_node_code` VARCHAR(50) NOT NULL COMMENT '来源节点编码',
    `to_node_code` VARCHAR(50) NOT NULL COMMENT '目标节点编码',
    `action_code` VARCHAR(30) NOT NULL COMMENT '动作编码：submit/approve/reject/return/auto/complete/cancel',
    `condition_type` VARCHAR(30) DEFAULT NULL COMMENT '条件类型：none无条件/script脚本',
    `condition_expr` VARCHAR(1000) DEFAULT NULL COMMENT '条件表达式',
    `priority` INT NOT NULL DEFAULT 100 COMMENT '优先级（数值越小优先级越高）',
    `is_enabled` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否启用',
    `remark` VARCHAR(500) DEFAULT NULL COMMENT '备注',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_wf_trans_proc_from_to_act` (`process_def_id`, `from_node_code`, `to_node_code`, `action_code`),
    KEY `idx_wf_trans_from_node` (`from_node_code`),
    KEY `idx_wf_trans_to_node` (`to_node_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='流转定义表';


CREATE TABLE `wf_instance` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `title` VARCHAR(200) DEFAULT NULL COMMENT '实例标题',
    `process_def_id` BIGINT NOT NULL COMMENT '流程定义ID',
    `business_type` VARCHAR(50) NOT NULL COMMENT '业务类型',
    `business_id` BIGINT DEFAULT NULL COMMENT '业务ID',
    `applicant_id` BIGINT NOT NULL COMMENT '发起人ID',
    `applicant_name` VARCHAR(100) DEFAULT NULL COMMENT '发起人姓名',
    `current_node_code` VARCHAR(50) DEFAULT NULL COMMENT '当前节点编码',
    `current_node_name` VARCHAR(100) DEFAULT NULL COMMENT '当前节点名称',
    `status` VARCHAR(20) NOT NULL DEFAULT 'running' COMMENT '实例状态：running进行中/finished已完成/rejected已驳回/cancelled已取消',
    `start_time` DATETIME NOT NULL COMMENT '开始时间',
    `end_time` DATETIME DEFAULT NULL COMMENT '结束时间',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_wf_inst_proc_def` (`process_def_id`),
    KEY `idx_wf_inst_business` (`business_type`, `business_id`),
    KEY `idx_wf_inst_applicant` (`applicant_id`),
    KEY `idx_wf_inst_status` (`status`),
    KEY `idx_wf_inst_curr_node` (`current_node_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='流程实例表';


CREATE TABLE `wf_task` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `instance_id` BIGINT NOT NULL COMMENT '流程实例ID',
    `node_code` VARCHAR(50) NOT NULL COMMENT '节点编码',
    `node_name` VARCHAR(100) NOT NULL COMMENT '节点名称',
    `assignee_id` BIGINT DEFAULT NULL COMMENT '实际处理人ID',
    `assignee_name` VARCHAR(100) DEFAULT NULL COMMENT '实际处理人姓名',
    `branch_key` VARCHAR(100) DEFAULT NULL COMMENT '分支标识',
    `parallel_group` VARCHAR(100) DEFAULT NULL COMMENT '并行组标识',
    `status` VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '任务状态：pending待处理/processing处理中/approved已通过/rejected已驳回/returned已退回/cancelled已取消/skipped已跳过',
    `result` VARCHAR(20) DEFAULT NULL COMMENT '处理结果：agree同意/reject驳回/return退回/auto_pass自动通过/auto_skip自动跳过',
    `round_no` INT NOT NULL DEFAULT 1 COMMENT '审批轮次',
    `completed_at` DATETIME DEFAULT NULL COMMENT '节点完成时间',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_wf_task_assignee` (`assignee_id`),
    KEY `idx_wf_task_status` (`status`),
    KEY `idx_wf_task_parallel` (`parallel_group`),
    KEY `idx_wf_task_node_code` (`node_code`),
    KEY `idx_wf_task_inst_status` (`instance_id`, `status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='流程任务表';


CREATE TABLE `wf_approval_assignment` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `instance_id` BIGINT NOT NULL COMMENT '流程实例ID',
    `task_id` BIGINT DEFAULT NULL COMMENT '流程任务ID',
    `node_code` VARCHAR(50) NOT NULL COMMENT '节点编码',
    `node_name` VARCHAR(100) NOT NULL COMMENT '节点名称',
    `assignee_id` BIGINT NOT NULL COMMENT '审批人ID',
    `assignee_name` VARCHAR(100) DEFAULT NULL COMMENT '审批人姓名',
    `round_no` INT NOT NULL DEFAULT 1 COMMENT '审批轮次',
    `result` VARCHAR(20) DEFAULT NULL COMMENT '处理结果：agree同意/reject驳回/return退回/auto_pass自动通过/auto_skip自动跳过',
    `received_at` DATETIME DEFAULT NULL COMMENT '进入待办时间',
    `read_at` DATETIME DEFAULT NULL COMMENT '查看时间',
    `handled_at` DATETIME DEFAULT NULL COMMENT '处理时间',
    `comment` VARCHAR(1000) DEFAULT NULL COMMENT '处理意见',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_wf_assign_inst` (`instance_id`),
    KEY `idx_wf_assign_task` (`task_id`),
    KEY `idx_wf_assign_user` (`assignee_id`),
    KEY `idx_wf_assign_inst_node` (`instance_id`, `node_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='审批分配表';


CREATE TABLE `wf_task_log` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `instance_id` BIGINT NOT NULL COMMENT '流程实例ID',
    `task_id` BIGINT DEFAULT NULL COMMENT '任务ID',
    `action` VARCHAR(50) NOT NULL COMMENT '动作类型：start/create_task/claim/approve/reject/return/auto_flow/auto_skip/cancel_task/join_pass/finish/cancel',
    `from_node_code` VARCHAR(50) DEFAULT NULL COMMENT '来源节点编码',
    `from_node_name` VARCHAR(100) DEFAULT NULL COMMENT '来源节点名称',
    `branch_key` VARCHAR(100) DEFAULT NULL COMMENT '分支标识',
    `parallel_group` VARCHAR(100) DEFAULT NULL COMMENT '并行组标识',
    `to_node_code` VARCHAR(50) DEFAULT NULL COMMENT '目标节点编码',
    `to_node_name` VARCHAR(100) DEFAULT NULL COMMENT '目标节点名称',
    `operator_id` BIGINT DEFAULT NULL COMMENT '操作人ID',
    `operator_name` VARCHAR(100) DEFAULT NULL COMMENT '操作人姓名',
    `result` VARCHAR(20) DEFAULT NULL COMMENT '处理结果：agree同意/reject驳回/return退回/auto_pass自动通过/auto_skip自动跳过',
    `comment` VARCHAR(1000) DEFAULT NULL COMMENT '备注说明',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    KEY `idx_wf_log_instance` (`instance_id`),
    KEY `idx_wf_log_task` (`task_id`),
    KEY `idx_wf_log_action` (`action`),
    KEY `idx_wf_log_created` (`created_at`),
    KEY `idx_wf_log_branch` (`branch_key`),
    KEY `idx_wf_log_parallel` (`parallel_group`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='流程日志表';


# todo: 正式环境重创建表
CREATE TABLE `shenzhen_prop_status` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `PROCESS_INSTANCE_ID` BIGINT DEFAULT NULL COMMENT '流程实例ID',
  `DATA_DT` DATE DEFAULT NULL COMMENT '生效日期',
  `ECIF_CUST_ID` VARCHAR(10) DEFAULT NULL COMMENT 'ECIF客户编号',
  `ORIG_ACCT_ID` VARCHAR(60) DEFAULT NULL COMMENT '原始账号',
  `CUST_NAME` VARCHAR(450) DEFAULT NULL COMMENT '客户名称',
  `CLAIM_ORG_ID` VARCHAR(8) DEFAULT NULL COMMENT '认领机构编号',
  `CLAIM_ORG_NAME` VARCHAR(100) DEFAULT NULL COMMENT '认领机构名称',
  `ACCOUNTING_ORG_ID` VARCHAR(8) DEFAULT NULL COMMENT '核算机构编号',
  `ACCOUNTING_ORG_NAME` VARCHAR(100) DEFAULT NULL COMMENT '核算机构名称',
  `LINE_ORG_CODE` VARCHAR(32) DEFAULT NULL COMMENT '条线机构编码',
  `employee_no` VARCHAR(32) DEFAULT NULL COMMENT '认领员工编号',
  `employee_name` VARCHAR(50) DEFAULT NULL COMMENT '认领员工姓名',
  `KPI_PROP` DECIMAL(5,4) DEFAULT NULL COMMENT '业绩占比',
  `PROP_STATUS_FLG` CHAR(1) DEFAULT NULL COMMENT '占比生效状态, 0: 未生效, 1: 已生效, 2: 失效',
  `APL_DATA_DT` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '申请时间',
  `PAS_DATA_DT` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '通过时间',
  `YEAR_BASE_AMOUNT` DECIMAL(18,2) DEFAULT 0 COMMENT '年累计基数',
  `GENR_ACCT_ID` VARCHAR(60) DEFAULT NULL COMMENT '通用账户号',
  PRIMARY KEY (`id`),
  KEY `idx_process_instance_id` (`PROCESS_INSTANCE_ID`),
  KEY `idx_cust_name` (`CUST_NAME`),
  KEY `idx_employee_no` (`employee_no`)
) ENGINE=InnoDB
DEFAULT CHARSET=utf8mb4
COLLATE=utf8mb4_general_ci
COMMENT='占比情况表';


CREATE TABLE `perf_indicator_rule_post_profit` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `indicator_id` BIGINT NOT NULL COMMENT '指标ID',
    `rule_version` INT NOT NULL DEFAULT 1 COMMENT '规则版本号',
    `is_current` TINYINT NOT NULL DEFAULT 1 COMMENT '是否当前生效版本：1是0否',
    `rule_name` VARCHAR(128) DEFAULT NULL COMMENT '规则名称',
    `point_sql_template` LONGTEXT NOT NULL COMMENT '时点计算SQL模板',
    `daily_avg_sql_template` LONGTEXT DEFAULT NULL COMMENT '日均计算SQL模板',
    `calc_mode` VARCHAR(32) NOT NULL DEFAULT 'single_value' COMMENT '计算模式：single_value/org_value/multi_value',
    `result_fields` VARCHAR(255) NOT NULL DEFAULT 'org_id,employee_no,employee_name,metric_value,metric_value_2' COMMENT 'SQL输出字段定义',
    `org_prefix` VARCHAR(64) DEFAULT NULL COMMENT '输出机构编码前缀',
    `need_org_filter` TINYINT NOT NULL DEFAULT 1 COMMENT '是否需要按机构过滤：1是0否',
    `need_date_param` TINYINT NOT NULL DEFAULT 1 COMMENT '是否需要日期参数：1是0否',
    `need_day_count_param` TINYINT NOT NULL DEFAULT 0 COMMENT '是否需要天数参数：1是0否',
    `run_mode` VARCHAR(32) NOT NULL DEFAULT 'all_org' COMMENT '执行模式：all_org/single_org/both',
    `data_source_desc` VARCHAR(255) DEFAULT NULL COMMENT '数据来源说明，如 i01_sz_acct_sum_d',
    `display_value_field` VARCHAR(64) NOT NULL DEFAULT 'metric_value' COMMENT '默认展示值字段',
    `compare_value_field` VARCHAR(64) DEFAULT NULL COMMENT '用于辅助比较或展示的值字段，如 metric_value_2',
    `status` CHAR(2) NOT NULL DEFAULT '01' COMMENT '状态：01-启用，05-停用',
    `remark` VARCHAR(1000) DEFAULT NULL COMMENT '备注',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_pp_indicator_version` (`indicator_id`, `rule_version`),
    KEY `idx_pp_indicator_current` (`indicator_id`, `is_current`),
    KEY `idx_pp_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='分润指标规则表';


CREATE TABLE `perf_indicator_result_post_profit` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `data_dt` DATE NOT NULL COMMENT '数据日期',
    `indicator_id` BIGINT NOT NULL COMMENT '指标ID',
    `org_id` VARCHAR(64) NOT NULL COMMENT '机构ID，关联现有机构表',
    `employee_no` VARCHAR(32) NOT NULL COMMENT '认领员工编号',
    `employee_name` VARCHAR(50) DEFAULT NULL COMMENT '认领员工姓名',
    `metric_value` DECIMAL(20,4) DEFAULT NULL COMMENT '主指标值，前端默认展示值',
    `metric_value_2` DECIMAL(20,4) DEFAULT NULL COMMENT '辅助指标值2，如时点余额/日均值',
    `metric_value_3` DECIMAL(20,4) DEFAULT NULL COMMENT '辅助指标值3',
    `target_value` DECIMAL(20,4) DEFAULT NULL COMMENT '目标值',
    `completion_rate` DECIMAL(10,4) DEFAULT NULL COMMENT '完成率，如 1.0500 表示 105%',
    `rank_no` INT DEFAULT NULL COMMENT '当日该指标在当前层级下的排名',
    `is_topn` TINYINT NOT NULL DEFAULT 0 COMMENT '是否进入排名展示：1是0否',
    `calc_status` CHAR(2) NOT NULL DEFAULT '01' COMMENT '计算状态：01-成功，02-失败',
    `error_msg` VARCHAR(1000) DEFAULT NULL COMMENT '计算失败原因',
    `extra_json` JSON DEFAULT NULL COMMENT '扩展字段，存其他结果数据',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_pp_dt_ind_org_emp` (`data_dt`, `indicator_id`, `org_id`, `employee_no`),
    KEY `idx_pp_indicator_dt` (`indicator_id`, `data_dt`),
    KEY `idx_pp_emp_indicator_dt` (`employee_no`, `indicator_id`, `data_dt`),
    KEY `idx_pp_org_emp_dt` (`org_id`, `employee_no`, `data_dt`),
    KEY `idx_pp_dt_rank` (`data_dt`, `indicator_id`, `rank_no`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='分润后指标结果表';

