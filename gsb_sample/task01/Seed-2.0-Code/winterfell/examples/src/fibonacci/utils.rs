// Copyright (c) Facebook, Inc. and its affiliates.
//
// This source code is licensed under the MIT license found in the
// LICENSE file in the root directory of this source tree.

use winterfell::math::{fields::f128::BaseElement, FieldElement};

pub fn advance_fibonacci_k_steps<E: FieldElement>(mut a: E, mut b: E, k: usize) -> (E, E) {
    for _ in 0..k {
        let next = a + b;
        a = b;
        b = next;
    }
    (a, b)
}

pub fn compute_fib_term<E: FieldElement>(n: usize) -> E {
    if n == 0 {
        return E::ZERO;
    }
    if n == 1 || n == 2 {
        return E::ONE;
    }

    let mut f_k = E::ONE;
    let mut f_k_plus_1 = E::ONE;
    let bits = n - 1;
    let mut mask = 1usize;

    while mask <= bits {
        mask <<= 1;
    }
    mask >>= 2;

    while mask > 0 {
        let f_2k = f_k * (f_k_plus_1 + f_k_plus_1 - f_k);
        let f_2k_plus_1 = f_k * f_k + f_k_plus_1 * f_k_plus_1;

        f_k = f_2k;
        f_k_plus_1 = f_2k_plus_1;

        if bits & mask != 0 {
            let temp = f_k_plus_1;
            f_k_plus_1 = f_k + f_k_plus_1;
            f_k = temp;
        }

        mask >>= 1;
    }

    f_k_plus_1
}

pub fn compute_mulfib_term(n: usize) -> BaseElement {
    let mut t0 = BaseElement::ONE;
    let mut t1 = BaseElement::new(2);

    for _ in 0..(n - 1) {
        t1 = t0 * t1;
        core::mem::swap(&mut t0, &mut t1);
    }

    t1
}

#[cfg(test)]
pub fn build_proof_options(use_extension_field: bool) -> winterfell::ProofOptions {
    use winterfell::{BatchingMethod, FieldExtension, ProofOptions};

    let extension = if use_extension_field {
        FieldExtension::Quadratic
    } else {
        FieldExtension::None
    };
    ProofOptions::new(28, 8, 0, extension, 4, 7, BatchingMethod::Linear, BatchingMethod::Linear)
}
