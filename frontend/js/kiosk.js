async function orderCoffee(
    recipeId
) {

    try {

        const response =
            await fetch(
                "/api/orders",
                {
                    method:
                        "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify({
                            recipe_id:
                                recipeId
                        })
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            showMessage(
                data.error
                || "주문 실패"
            );

            return;
        }


        myOrderId =
            data.order_id;


        document
            .getElementById(
                "order-id"
            )
            .textContent =
            data.order_id;


        document
            .getElementById(
                "order-name"
            )
            .textContent =
            data.recipe_name;


        document
            .getElementById(
                "order-status"
            )
            .textContent =
            data.queue_position > 0
                ? "대기 " + data.queue_position + "번째"
                : "제조 중";


    } catch (error) {

        console.error(
            error
        );

        showMessage(
            "서버 연결 오류"
        );
    }
}


async function sendControl(
    command
) {

    if (!command) {
        return;
    }

    try {

        const response =
            await fetch(
                "/api/control/" + command,
                { method: "POST" }
            );

        const data =
            await response.json();

        if (!response.ok) {
            showMessage(data.error || "제어 명령 실패");
            return;
        }

        if (!data.success) {
            showMessage(data.message || "제어 명령 거절");
        }

    } catch (error) {

        console.error(
            error
        );

        showMessage(
            "서버 연결 오류"
        );
    }
}


function showMessage(
    text
) {

    document
        .getElementById(
            "process-message"
        )
        .textContent =
        text;
}


for (const id of ["btn-pause", "btn-force", "btn-start"]) {

    document
        .getElementById(id)
        .addEventListener(
            "click",
            function() {
                sendControl(this.dataset.command);
            }
        );
}
