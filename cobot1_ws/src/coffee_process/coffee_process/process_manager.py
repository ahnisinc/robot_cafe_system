class ProcessManager:

    def __init__(
        self,
        recipe_manager,
        executor,
    ):

        self.recipe_manager = recipe_manager
        self.executor       = executor
        self.running        = False

    def execute_recipe(
        self,
        recipe_id,
        on_step=None,
    ):

        recipe       = self.recipe_manager.load_recipe(recipe_id)
        steps        = recipe["steps"]
        self.running = True

        try:
            total = len(steps)

            for index, step in enumerate(steps):
                if on_step:
                    on_step(
                        index,
                        total,
                        step,
                    )

                self.executor.execute_step(step)

        finally:
            self.running = False
