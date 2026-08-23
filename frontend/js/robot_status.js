const socket =
    io();


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


        if (
            data.order_id
        ) {

            document
                .getElementById(
                    "order-id"
                )
                .textContent =
                    data.order_id;
        }

    }
);
