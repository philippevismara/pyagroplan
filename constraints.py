from abc import ABC, abstractmethod


class Constraint(ABC):
    def __init__(self):
        raise NotImplementedError()

    @abstractmethod
    def post(self, model): ...


class CropRotationConstraint(Constraint):
    def __init__(self):
        raise NotImplementedError()

    def post(self, model):
        raise NotImplementedError()


class ForbidNegativeInteractionsConstraint(Constraint):
    def __init__(self):
        raise NotImplementedError()

    def post(self, model):
        raise NotImplementedError()


class DiluteSpeciesConstraint(Constraint):
    def __init__(self):
        raise NotImplementedError()

    def post(self, model):
        raise NotImplementedError()


class DiluteFamilyConstraint(Constraint):
    def __init__(self):
        raise NotImplementedError()

    def post(self, model):
        raise NotImplementedError()


class GroupIdenticalCropsConstraint(Constraint):
    def __init__(self):
        raise NotImplementedError()

    def post(self, model):
        raise NotImplementedError()


class InteractionConstraint(Constraint):
    def __init__(self):
        raise NotImplementedError()

    def post(self, model):
        raise NotImplementedError()


class ForbidNegativePrecedencesConstraint(Constraint):
    def __init__(self):
        raise NotImplementedError()

    def post(self, model):
        raise NotImplementedError()


"""
TODO

public:
postInteractionReifTable
postInteractionReifBased

private:
postInteractionCountBased
postInteractionCustomPropBased
postInteractionGraphBased
"""
