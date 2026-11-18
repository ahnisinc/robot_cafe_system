const socket =
    io();


const CONTROL_LAYOUT = {
    IDLE:      { pause: ["정지", null],      force: ["강제 정지", null],         start: ["시작", null] },
    RUNNING:   { pause: ["정지", "pause"],   force: ["강제 정지", "force_stop"], start: ["시작", null] },
    PAUSED:    { pause: ["재개", "resume"],  force: ["강제 정지", "force_stop"], start: ["시작", null] },
    STOPPED:   { pause: ["정지", null],      force: ["재개", "resume"],          start: ["시작", null] },
    RESETTING: { pause: ["정지", null],      force: ["강제 정지", "force_stop"], start: ["시작", null] },
    HOMED:     { pause: ["정지", null],      force: ["강제 정지", null],         start: ["시작", "start"] },
};

const STATE_LABELS = {
    IDLE: "주문 대기",
    RUNNING: "제조 중",
    PAUSED: "일시정지",
    STOPPED: "강제 정지 (초기화 필요)",
    RESETTING: "초기화 중",
    HOMED: "시작 대기",
};

const ORDER_STATE_LABELS = {
    RUNNING: "제조 중",
    DONE: "완료",
    FAILED: "실패",
};


let myOrderId = null;


function controlLayout(state) {

    return CONTROL_LAYOUT[state]
        || { pause: ["정지", null], force: ["강제 정지", null], start: ["시작", null] };
}


function renderControls(state) {

    const layout = controlLayout(state);

    for (const [key, id] of [["pause", "btn-pause"], ["force", "btn-force"], ["start", "btn-start"]]) {

        const button = document.getElementById(id);
        const [label, command] = layout[key];

        button.textContent = label;
        button.disabled = command === null;
        button.dataset.command = command || "";
        button.classList.toggle("resume", command === "resume");
    }
}


socket.on(
    "server_status",
    function(data) {

        if (
            data.connected
        ) {

            document
                .getElementById(
                    "robot-state"
                )
                .textContent =
                    "SERVER CONNECTED";
        }
    }
);


socket.on(
    "coffee_progress",
    function(data) {

        const progress =
            Number(
                data.progress || 0
            );


        document
            .getElementById(
                "progress-fill"
            )
            .style.width =
                progress + "%";


        document
            .getElementById(
                "progress-text"
            )
            .textContent =
                progress.toFixed(0)
                + "%";


        document
            .getElementById(
                "process-step"
            )
            .textContent =
                data.current_step
                || data.state
                || "대기 중";


        document
            .getElementById(
                "process-message"
            )
            .textContent =
                data.message || "";


        document
            .getElementById(
                "robot-state"
            )
            .textContent =
                STATE_LABELS[data.state] || data.state || "ROBOT STANDBY";


        renderControls(data.state);


        if (
            myOrderId
            && data.order_id === myOrderId
            && ORDER_STATE_LABELS[data.order_state]
        ) {

            document
                .getElementById(
                    "order-status"
                )
                .textContent =
                    ORDER_STATE_LABELS[data.order_state];
        }

    }
);


if (typeof module !== "undefined") {
    module.exports = { controlLayout };
}
