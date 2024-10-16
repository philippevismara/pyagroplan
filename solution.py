import pandas as pd


class Solution:
    def __init__(self, crops_calendar, variables):
        self.crops_calendar = crops_calendar
        self.variables = variables

        self.variables_names = [var.name for var in variables]
        self.variables_values = [var.get_value() for var in variables]
        # TODO self.variables = choco_solution.retrieveIntVars()

        self.crops_planning = pd.DataFrame({
            "crops_names": self.crops_calendar.crops_names,
            "assignment": self.variables_values
        })

    def __len__(self):
        return len(self.crops_planning)

    def __str__(self):
        return "Solution:\n{}".format(self.crops_planning)

    def to_csv(self, filename):
        raise NotImplementedError()
