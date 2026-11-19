string order_id
string recipe_id
string state
string current_step

int32 current_step_index
int32 total_steps

float32 progress

string message

# 주문 상태: RUNNING / DONE / FAILED / "" (다음 주문 시작 전까지 마지막 값 유지)
string order_state
