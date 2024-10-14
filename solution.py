class Solution:
    def __init__(self, variables):
        self.variables = variables
        self.values = {var.name: var.get_value() for var in variables}
        # TODO self.variables = choco_solution.retrieveIntVars()

    def __str__(self):
        return "Solution: {}".format(self.values)

    def __len__(self):
        return len(self.values)

    def to_csv(self, filename):
        raise NotImplementedError()
