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

            alert(
                data.error
                || "주문 실패"
            );

            return;
        }


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


    } catch (error) {

        console.error(
            error
        );

        alert(
            "서버 연결 오류"
        );
    }
}


function emergencyStop() {

    alert(
        "EMERGENCY STOP 요청"
    );

    /*
     * 실제 구현에서는 여기서
     * Flask API -> ROSBridge ->
     * robot_control STOP service
     * 로 연결한다.
     */
}
