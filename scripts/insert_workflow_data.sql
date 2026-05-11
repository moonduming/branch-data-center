# workflow 初始化数据
# 说明：
# 1. 仅插入三条流程定义：报表报送流程、业绩认领流程、业绩移交流程
# 2. 节点审核人规则中的 rule_type / rule_value 先占位，后续可按实际需求调整
# 3. 该脚本可重复执行，会先按流程编码清理旧数据再重新插入

START TRANSACTION;

# =========================
# 1. 清理旧数据
# =========================

DELETE FROM wf_node_assignee_rule
WHERE process_def_id IN (
    SELECT id FROM (
        SELECT id FROM wf_process_def WHERE process_code IN ('rpt_submit', 'perf_claim', 'perf_transfer')
    ) t
);

DELETE FROM wf_transition_def
WHERE process_def_id IN (
    SELECT id FROM (
        SELECT id FROM wf_process_def WHERE process_code IN ('rpt_submit', 'perf_claim', 'perf_transfer')
    ) t
);

DELETE FROM wf_node_def
WHERE process_def_id IN (
    SELECT id FROM (
        SELECT id FROM wf_process_def WHERE process_code IN ('rpt_submit', 'perf_claim', 'perf_transfer')
    ) t
);

DELETE FROM wf_process_def
WHERE process_code IN ('rpt_submit', 'perf_claim', 'perf_transfer');

# =========================
# 2. 插入流程定义
# =========================

INSERT INTO wf_process_def (process_code, process_name, business_type, version, status, is_latest, remark) VALUES
('rpt_submit', '报表报送流程', 'report_submit', 1, 'active', 1, '根据流程图初始化的报表报送流程'),
('perf_claim', '业绩认领流程', 'performance_claim', 1, 'active', 1, '根据流程图初始化的业绩认领流程'),
('perf_transfer', '业绩移交流程', 'performance_transfer', 1, 'active', 1, '根据流程图初始化的业绩移交流程');

SET @proc_rpt_submit_id := (SELECT id FROM wf_process_def WHERE process_code = 'rpt_submit' AND version = 1 LIMIT 1);
SET @proc_perf_claim_id := (SELECT id FROM wf_process_def WHERE process_code = 'perf_claim' AND version = 1 LIMIT 1);
SET @proc_perf_transfer_id := (SELECT id FROM wf_process_def WHERE process_code = 'perf_transfer' AND version = 1 LIMIT 1);

# =========================
# 3. 插入节点定义
# =========================

INSERT INTO wf_node_def (process_def_id, node_code, node_name, node_type, node_order, is_parallel, parallel_mode, join_strategy, can_reject, can_return, auto_create_task, remark, auto_func_name) VALUES
(@proc_rpt_submit_id, 'rpt_submit_select_unit', '流程制定人选择报送单位', 'start', 10, 0, NULL, NULL, 0, 0, 1, '报表报送流程发起节点', NULL),
(@proc_rpt_submit_id, 'rpt_submit_parallel_check', '并行度判断', 'auto', 20, 0, NULL, NULL, 0, 0, 0, '代码自动判断并行度', 'report_parallel_split'),
(@proc_rpt_submit_id, 'rpt_submit_unit', '单位', 'manual', 30, 1, NULL, NULL, 0, 1, 1, '报表报送流程并行节点', NULL),
(@proc_rpt_submit_id, 'rpt_submit_checker_confirm', '确认单位复核人', 'auto', 40, 0, NULL, NULL, 0, 0, 0, '根据上一节点审批人团队自动确认单位复核人', 'report_confirm_checker'),
(@proc_rpt_submit_id, 'rpt_submit_checker', '单位复核人', 'manual', 50, 0, NULL, NULL, 0, 1, 1, '报表报送流程复核节点', NULL),
(@proc_rpt_submit_id, 'rpt_submit_owner', '单位负责人', 'manual', 60, 0, NULL, NULL, 0, 1, 1, '报表报送流程负责人节点', NULL),
(@proc_rpt_submit_id, 'rpt_submit_summary', '流程制定人汇总', 'manual', 70, 0, NULL, 'all_pass', 1, 1, 1, '报表报送流程汇总节点', NULL),
(@proc_rpt_submit_id, 'rpt_submit_end', '结束', 'end', 80, 0, NULL, NULL, 0, 0, 0, '报表报送流程结束节点', NULL),

(@proc_perf_claim_id, 'perf_claim_apply', '申请人', 'start', 10, 0, NULL, NULL, 0, 0, 1, '业绩认领流程发起节点', NULL),
(@proc_perf_claim_id, 'perf_claim_parallel_check', '并行度判断', 'auto', 20, 0, NULL, NULL, 0, 0, 0, '代码自动判断并行度', 'claim_parallel_split'),
(@proc_perf_claim_id, 'perf_claim_org_leader', '机构负责人审批', 'manual', 30, 1, NULL, NULL, 1, 0, 1, '业绩认领流程并行审批节点', NULL),
(@proc_perf_claim_id, 'perf_claim_share_check', '判断分支数量', 'auto', 40, 0, NULL, 'all_pass', 0, 0, 0, '代码自动判断并行数量和后续分支', 'claim_parallel_merge_check'),
(@proc_perf_claim_id, 'perf_claim_operator_assign', '自动确认经办人', 'auto', 45, 0, NULL, NULL, 0, 0, 0, '根据条线机构自动确认经办人', 'assign_personal_line_assignee'),
(@proc_perf_claim_id, 'perf_claim_operator', '经办人', 'manual', 50, 0, NULL, NULL, 1, 0, 1, '经办人审批节点，正常由自动节点确认审批人', NULL),
(@proc_perf_claim_id, 'perf_claim_superior', '上级条线审批人', 'manual', 60, 0, NULL, NULL, 1, 0, 1, '业绩认领流程审批节点', NULL),
(@proc_perf_claim_id, 'perf_claim_end', '结束', 'end', 70, 0, NULL, NULL, 0, 0, 0, '业绩认领流程结束节点', NULL),

(@proc_perf_transfer_id, 'perf_transfer_apply', '申请人', 'start', 10, 0, NULL, NULL, 0, 0, 1, '业绩移交流程发起节点', NULL),
(@proc_perf_transfer_id, 'perf_transfer_parallel_check', '并行度判断', 'auto', 20, 0, NULL, NULL, 0, 0, 0, '代码自动判断并行度', 'claim_parallel_split'),
(@proc_perf_transfer_id, 'perf_transfer_org_leader', '机构负责人审批', 'manual', 30, 1, NULL, NULL, 1, 0, 1, '业绩移交流程并行审批节点', NULL),
(@proc_perf_transfer_id, 'perf_transfer_operator_assign', '自动确认经办人', 'auto', 40, 0, NULL, NULL, 0, 0, 0, '根据条线机构自动确认经办人', 'assign_personal_line_assignee'),
(@proc_perf_transfer_id, 'perf_transfer_operator', '经办人', 'manual', 50, 0, NULL, 'all_pass', 1, 0, 1, '经办人汇总审批节点，正常由自动节点确认审批人', NULL),
(@proc_perf_transfer_id, 'perf_transfer_superior', '上级条线审批人', 'manual', 60, 0, NULL, NULL, 1, 0, 1, '业绩移交流程审批节点', NULL),
(@proc_perf_transfer_id, 'perf_transfer_end', '结束', 'end', 70, 0, NULL, NULL, 0, 0, 0, '业绩移交流程结束节点', NULL);

# =========================
# 4. 插入流转定义
# =========================

INSERT INTO wf_transition_def (process_def_id, from_node_code, to_node_code, action_code, condition_type, condition_expr, priority, is_enabled, remark) VALUES
(@proc_rpt_submit_id, 'rpt_submit_select_unit', 'rpt_submit_parallel_check', 'submit', 'none', 'true', 10, 1, '提交流转到并行度判断节点'),
(@proc_rpt_submit_id, 'rpt_submit_parallel_check', 'rpt_submit_unit', 'auto', 'none', 'true', 20, 1, '并行度确定并行量后流转到单位节点'),
(@proc_rpt_submit_id, 'rpt_submit_unit', 'rpt_submit_checker_confirm', 'approve', 'none', 'true', 30, 1, '单位处理完成后先自动确认单位复核人'),
(@proc_rpt_submit_id, 'rpt_submit_unit', 'rpt_submit_end', 'reject', 'none', 'true', 35, 1, '单位节点驳回结束任务'),
(@proc_rpt_submit_id, 'rpt_submit_checker_confirm', 'rpt_submit_checker', 'auto', 'none', 'true', 38, 1, '自动确认单位复核人后流转至单位复核节点'),
(@proc_rpt_submit_id, 'rpt_submit_checker', 'rpt_submit_owner', 'approve', 'none', 'true', 40, 1, '单位复核后流转至单位负责人'),
(@proc_rpt_submit_id, 'rpt_submit_checker', 'rpt_submit_unit', 'return', 'none', 'true', 45, 1, '单位复核退回给单位节点'),
(@proc_rpt_submit_id, 'rpt_submit_owner', 'rpt_submit_summary', 'approve', 'none', 'true', 50, 1, '单位负责人审批后流转至汇总节点'),
(@proc_rpt_submit_id, 'rpt_submit_owner', 'rpt_submit_unit', 'return', 'none', 'true', 55, 1, '单位负责人退回给单位节点'),
(@proc_rpt_submit_id, 'rpt_submit_summary', 'rpt_submit_end', 'complete', 'none', 'true', 50, 1, '汇总完成后结束流程'),
(@proc_rpt_submit_id, 'rpt_submit_summary', 'rpt_submit_unit', 'return', 'none', 'true', 55, 1, '汇总退回给单位节点'),
(@proc_rpt_submit_id, 'rpt_submit_summary', 'rpt_submit_end', 'reject', 'none', 'true', 60, 1, '汇总节点驳回结束任务'),
(@proc_perf_claim_id, 'perf_claim_apply', 'perf_claim_parallel_check', 'submit', 'none', 'true', 10, 1, '申请后先进入并行度自动判断'),
(@proc_perf_claim_id, 'perf_claim_parallel_check', 'perf_claim_org_leader', 'auto', 'none', 'true', 20, 1, '并行判断节点占位，默认流转到机构负责人节点'),
(@proc_perf_claim_id, 'perf_claim_org_leader', 'perf_claim_share_check', 'approve', 'none', 'true', 30, 1, '机构负责人审批后进入分润判断'),
(@proc_perf_claim_id, 'perf_claim_org_leader', 'perf_claim_end', 'reject', 'none', 'true', 35, 1, '机构负责人驳回'),
(@proc_perf_claim_id, 'perf_claim_share_check', 'perf_claim_operator_assign', 'auto', 'none', NULL, 40, 1, '多分支时先自动确认经办人'),
(@proc_perf_claim_id, 'perf_claim_operator_assign', 'perf_claim_operator', 'auto', 'none', 'true', 45, 1, '自动确认经办人后流转至经办人节点'),
(@proc_perf_claim_id, 'perf_claim_operator', 'perf_claim_superior', 'approve', 'none', 'true', 50, 1, '经办人转至上级条线审批人'),
(@proc_perf_claim_id, 'perf_claim_operator', 'perf_claim_end', 'reject', 'none', 'true', 55, 1, '经办人驳回'),
(@proc_perf_claim_id, 'perf_claim_share_check', 'perf_claim_end', 'auto', 'none', NULL, 60, 1, '单分支时直接结束'),
(@proc_perf_claim_id, 'perf_claim_superior', 'perf_claim_end', 'complete', 'none', 'true', 70, 1, '上级条线审批完成后结束流程'),
(@proc_perf_claim_id, 'perf_claim_superior', 'perf_claim_end', 'reject', 'none', 'true', 75, 1, '上级条线审批驳回'),
(@proc_perf_transfer_id, 'perf_transfer_apply', 'perf_transfer_parallel_check', 'submit', 'none', 'true', 10, 1, '申请后先进入并行度自动判断'),
(@proc_perf_transfer_id, 'perf_transfer_parallel_check', 'perf_transfer_org_leader', 'auto', 'none', 'true', 20, 1, '并行判断节点占位，默认流转到机构负责人节点'),
(@proc_perf_transfer_id, 'perf_transfer_org_leader', 'perf_transfer_operator_assign', 'approve', 'none', 'true', 30, 1, '机构负责人审批后先自动确认经办人'),
(@proc_perf_transfer_id, 'perf_transfer_org_leader', 'perf_transfer_end', 'reject', 'none', 'true', 35, 1, '机构负责人驳回'),
(@proc_perf_transfer_id, 'perf_transfer_operator_assign', 'perf_transfer_operator', 'auto', 'none', 'true', 40, 1, '自动确认经办人后流转至经办人节点'),
(@proc_perf_transfer_id, 'perf_transfer_operator', 'perf_transfer_superior', 'approve', 'none', 'true', 40, 1, '经办人转至上级条线审批人'),
(@proc_perf_transfer_id, 'perf_transfer_operator', 'perf_transfer_end', 'reject', 'none', 'true', 45, 1, '经办人驳回'),
(@proc_perf_transfer_id, 'perf_transfer_superior', 'perf_transfer_end', 'complete', 'none', 'true', 50, 1, '上级条线审批完成后结束流程'),
(@proc_perf_transfer_id, 'perf_transfer_superior', 'perf_transfer_end', 'reject', 'none', 'true', 55, 1, '上级条线审批驳回');

# =========================
# 5. 插入节点审核人规则
# =========================

INSERT INTO wf_node_assignee_rule (process_def_id, node_code, rule_type, rule_value, remark) VALUES
(@proc_rpt_submit_id, 'rpt_submit_select_unit', 'applicant', '', '流程制定人选择报送单位，发起人本人'),
(@proc_rpt_submit_id, 'rpt_submit_unit', 'employee_level', '15,25', '单位并行节点，按员工级别'),
(@proc_rpt_submit_id, 'rpt_submit_checker', 'employee_level', '13,23', '单位复核人，按员工级别'),
(@proc_rpt_submit_id, 'rpt_submit_owner', 'employee_level', '10,20', '单位负责人，按员工级别'),
(@proc_rpt_submit_id, 'rpt_submit_summary', 'applicant', '', '流程制定人汇总，发起人本人'),
(@proc_perf_claim_id, 'perf_claim_apply', 'applicant', '', '申请人节点，发起人本人'),
(@proc_perf_claim_id, 'perf_claim_org_leader', 'employee_level', '10', '机构负责人并行审批，按员工级别'),
(@proc_perf_claim_id, 'perf_claim_operator', 'fixed_user', '32', '经办人审批兜底规则，正常由自动节点确认审批人'),
(@proc_perf_claim_id, 'perf_claim_superior', 'employee_level', '10', '上级条线审批人，按员工级别'),
(@proc_perf_transfer_id, 'perf_transfer_apply', 'applicant', '', '申请人节点，发起人本人'),
(@proc_perf_transfer_id, 'perf_transfer_org_leader', 'employee_level', '10', '机构负责人并行审批，按员工级别'),
(@proc_perf_transfer_id, 'perf_transfer_operator', 'fixed_user', '32', '经办人审批兜底规则，正常由自动节点确认审批人'),
(@proc_perf_transfer_id, 'perf_transfer_superior', 'employee_level', '10', '上级条线审批人，按员工级别');

COMMIT;
