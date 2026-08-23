class SafetyManager:

    def validate_motion(
        self,
        connected,
        emergency_stopped,
    ):

        if not connected:

            raise RuntimeError(
                "Robot is not connected"
            )

        if emergency_stopped:

            raise RuntimeError(
                "Emergency stop is active"
            )

        return True
