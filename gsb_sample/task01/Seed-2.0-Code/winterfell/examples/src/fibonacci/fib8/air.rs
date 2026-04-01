// Copyright (c) Facebook, Inc. and its affiliates.
//
// This source code is licensed under the MIT license found in the
// LICENSE file in the root directory of this source tree.

use winterfell::{
    Air, AirContext, Assertion, EvaluationFrame, ProofOptions, TraceInfo,
    TransitionConstraintDegree,
};

use super::{BaseElement, FieldElement, TRACE_WIDTH};
use crate::fibonacci::utils::{advance_fibonacci_k_steps, compute_fib_term};
use crate::utils::are_equal;

// FIBONACCI AIR
// ================================================================================================

pub struct Fib8Air {
    context: AirContext<BaseElement>,
    result: BaseElement,
}

impl Air for Fib8Air {
    type BaseField = BaseElement;
    type PublicInputs = BaseElement;

    // CONSTRUCTOR
    // --------------------------------------------------------------------------------------------
    fn new(trace_info: TraceInfo, pub_inputs: Self::BaseField, options: ProofOptions) -> Self {
        let degrees = vec![TransitionConstraintDegree::new(1), TransitionConstraintDegree::new(1)];
        assert_eq!(TRACE_WIDTH, trace_info.width());
        Fib8Air {
            context: AirContext::new(trace_info, degrees, 3, options),
            result: pub_inputs,
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
        debug_assert_eq!(TRACE_WIDTH, next.len());

        let (expected0, expected1) = advance_fibonacci_k_steps(current[0], current[1], 8);
        result[0] = are_equal(next[0], expected0);
        result[1] = are_equal(next[1], expected1);
    }

    fn get_assertions(&self) -> Vec<Assertion<Self::BaseField>> {
        // assert that the trace starts with 7th and 8th terms of Fibonacci sequence (the first
        // 6 terms are not recorded in the trace), and ends with the expected result
        let last_step = self.trace_length() - 1;
        let fib7 = compute_fib_term::<BaseElement>(7);
        let fib8 = compute_fib_term::<BaseElement>(8);
        vec![
            Assertion::single(0, 0, fib7),
            Assertion::single(1, 0, fib8),
            Assertion::single(1, last_step, self.result),
        ]
    }
}
