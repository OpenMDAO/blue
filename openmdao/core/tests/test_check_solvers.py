
import unittest
import numpy as np
from six import text_type, PY3
from six.moves import cStringIO
import warnings

from openmdao.api import ImplicitComponent, Problem, Group, IndepVarComp, ExecComp, ScipyKrylov
from openmdao.test_suite.components.sellar import StateConnection


class StateConnWithSolveLinear(StateConnection):
    def solve_linear(self, dumat, drmat, vois, mode=None):
        pass


class TestProblemCheckSolvers(unittest.TestCase):

    def test_state_single(self):
        prob = Problem()
        prob.model.add_subsystem('statecomp', StateConnection())

        try:
            prob.setup()
        except Exception as err:
            self.assertTrue("Group '' has a LinearRunOnce solver but it contains "
                            "implicit outputs ['statecomp.y2_command']. To fix "
                            "this error, change to a different linear solver, "
                            "e.g. ScipyKrylov or PETScKrylov." in str(err))
        else:
            self.fail("Exception expected")

    def test_state_single_w_ancestor_iter(self):
        prob = Problem()
        model = prob.model

        model.add_subsystem("G1", Group())
        model.G1.add_subsystem('statecomp', StateConnection())

        model.linear_solver.options['maxiter'] = 5

        # should be no exception here since top level solver has maxiter > 1
        results = prob.setup()

    def test_state_not_single(self):
        prob = Problem()
        model = prob.model
        model.linear_solver = ScipyKrylov()

        model.add_subsystem('statecomp', StateConnection())
        model.add_subsystem('C1', ExecComp('y=2.0*x'))

        prob.setup()  # should be no exception here

    def test_state_single_maxiter_gt_1(self):
        prob = Problem()
        model = prob.model
        model.linear_solver.options['maxiter'] = 2

        model.add_subsystem('statecomp', StateConnection())

        # this should not raise an exception because maxiter > 1
        prob.setup()

    def test_state_single_solve_linear(self):
        # this comp has its own solve_linear method, so there should be
        # no exceptions or layout recommendations made here.
        prob = Problem()
        model = prob.model

        model.add_subsystem('statecomp', StateConnWithSolveLinear())

        prob.setup()
        # self.assertTrue('has implicit states' not in s.getvalue())

    def test_cycle(self):
        prob = Problem()
        model = prob.model
        model.linear_solver.options['maxiter'] = 1

        model.add_subsystem("C1", ExecComp('y=2.0*x'))
        model.add_subsystem("C2", ExecComp('y=2.0*x'))
        model.add_subsystem("C3", ExecComp('y=2.0*x'))

        model.connect('C1.y','C2.x')
        model.connect('C2.y','C3.x')
        model.connect('C3.y','C1.x')

        try:
            prob.setup()
        except Exception as err:
            self.assertTrue("Group '' has a LinearRunOnce solver but it "
                            "contains cycles [['C1', 'C2', 'C3']]. To fix "
                            "this error, change to a different linear solver, "
                            "e.g. ScipyKrylov or PETScKrylov." in str(err))
        else:
            self.fail("Exception expected")

    def test_cycle_maxiter_gt_1(self):
        prob = Problem()
        model = prob.model
        model.linear_solver.options['maxiter'] = 2

        C1 = model.add_subsystem("C1", ExecComp('y=2.0*x'))
        C2 = model.add_subsystem("C2", ExecComp('y=2.0*x'))
        C3 = model.add_subsystem("C3", ExecComp('y=2.0*x'))

        model.connect('C1.y','C2.x')
        model.connect('C2.y','C3.x')
        model.connect('C3.y','C1.x')

        # this should not raise an exception because maxiter > 1
        prob.setup()

    def test_cycle_maxiter_gt_1_subgroup(self):
        prob = Problem()
        model = prob.model
        model.linear_solver.options['maxiter'] = 2

        G1 = model.add_subsystem("G1", Group())
        C1 = G1.add_subsystem("C1", ExecComp('y=2.0*x'))
        C2 = G1.add_subsystem("C2", ExecComp('y=2.0*x'))
        C3 = G1.add_subsystem("C3", ExecComp('y=2.0*x'))

        G1.connect('C1.y','C2.x')
        G1.connect('C2.y','C3.x')
        G1.connect('C3.y','C1.x')

        # this should not raise an exception because maxiter > 1 in an ancestor group
        prob.setup()


if __name__ == "__main__":
    unittest.main()
