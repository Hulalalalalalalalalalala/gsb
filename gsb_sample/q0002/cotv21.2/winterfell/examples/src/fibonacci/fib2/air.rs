// Copyright (c) Facebook, Inc. and its affiliates.
//
// This source code is licensed under the MIT license found in the
// LICENSE file in the root directory of this source tree.

use winterfell::{
    math::ToElements, Air, AirContext, Assertion, EvaluationFrame, TraceInfo,
    TransitionConstraintDegree,
};

use super::{BaseElement, FieldElement, ProofOptions, TRACE_WIDTH};
use crate::utils::are_equal;

// PUBLIC INPUTS
// ================================================================================================

#[derive(Clone)]
pub struct FibInputs {
    pub a0: BaseElement,
    pub a1: BaseElement,
    pub result: BaseElement,
}

impl ToElements<BaseElement> for FibInputs {
    fn to_elements(&self) -> Vec<BaseElement> {
        vec![self.a0, self.a1, self.result]
    }
}

// FIBONACCI AIR
// ================================================================================================

pub struct FibAir {
    context: AirContext<BaseElement>,
    result: BaseElement,
    a0: BaseElement,
    a1: BaseElement,
}

impl Air for FibAir {
    type BaseField = BaseElement;
    type PublicInputs = FibInputs;

    // CONSTRUCTOR
    // --------------------------------------------------------------------------------------------
    fn new(trace_info: TraceInfo, pub_inputs: Self::PublicInputs, options: ProofOptions) -> Self {
        let degrees = vec![TransitionConstraintDegree::new(1), TransitionConstraintDegree::new(1)];
        assert_eq!(TRACE_WIDTH, trace_info.width());
        FibAir {
            context: AirContext::new(trace_info, degrees, 3, options),
            result: pub_inputs.result,
            a0: pub_inputs.a0,
            a1: pub_inputs.a1,
        }
    }

    fn context(&self) -> &AirContext<Self::BaseField> {
        &self.context
    }

    fn evaluate_transition<E: FieldElement + From<Self::BaseField>>(
        &self,
        frame: &EvaluationFrame<E>,
        _periodic_values: &[E],
        result: &mut [E],
    ) {
        let current = frame.current();
        let next = frame.next();
        // expected state width is 2 field elements
        debug_assert_eq!(TRACE_WIDTH, current.len());
        debug_assert_eq!(TRACE_WIDTH, current.len());
        debug_assert_eq!(TRACE_WIDTH, next.len());

        // constraints of Fibonacci sequence (2 terms per step):
        // s_{0, i+1} = s_{0, i} + s_{1, i}
        // s_{1, i+1} = s_{1, i} + s_{0, i+1}
        result[0] = are_equal(next[0], current[0] + current[1]);
        result[1] = are_equal(next[1], current[1] + next[0]);
    }

    fn get_assertions(&self) -> Vec<Assertion<Self::BaseField>> {
        // a valid Fibonacci sequence should start with two ones and terminate with
        // the expected result
        let last_step = self.trace_length() - 1;
        vec![
            Assertion::single(0, 0, self.a0),
            Assertion::single(1, 0, self.a1),
            Assertion::single(1, last_step, self.result),
        ]
    }
}
