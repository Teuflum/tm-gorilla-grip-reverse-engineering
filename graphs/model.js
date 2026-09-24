// Values for the tested Trackmania physics build, summarized in the report.
// Inputs and outputs are fractions (0..1) unless a function says otherwise.
(function (root, factory) {
  const model = factory();
  if (typeof module === 'object' && module.exports) module.exports = model;
  root.GorillaGripModel = model;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  const icePoints = [[0, 0], [0.05, 0.6], [0.2, 0.85], [1, 1]];
  const otherPoints = [[0, 0], [0.8, 0.3], [0.95, 0.7], [1, 1]];

  function clamp(value, low = 0, high = 1) {
    return Math.min(high, Math.max(low, value));
  }

  function interpolate(points, x) {
    const input = clamp(x, points[0][0], points[points.length - 1][0]);
    for (let i = 1; i < points.length; i++) {
      const [x1, y1] = points[i];
      if (input <= x1) {
        const [x0, y0] = points[i - 1];
        return y0 + (input - x0) * (y1 - y0) / (x1 - x0);
      }
    }
    return points[points.length - 1][1];
  }

  function iceWeight(icing) { return interpolate(icePoints, icing); }
  function otherWeight(icing) { return interpolate(otherPoints, icing); }
  function ordinaryWeight(icing, material) {
    return 1 - (material === 'ice' ? iceWeight(icing) : otherWeight(icing));
  }

  // A single wheel held in one state. The wetness floor is fixed at the
  // transition into decay; this deliberately does not simulate wetness drying.
  function icingAt(state, startingIcing, elapsedMs, wetness) {
    const initial = clamp(startingIcing);
    const time = Math.max(0, elapsedMs);
    if (state === 'ice') return clamp(initial + time / 1650);
    const floor = Math.min(initial, clamp(wetness));
    if (state === 'plastic') return Math.max(floor, clamp(initial - time / 3300));
    if (state === 'air') return Math.max(floor, clamp(initial - time / 6000));
    throw new Error(`Unknown icing state: ${state}`);
  }

  // Full-left to full-right in the measured ice-contact condition.
  function steeringAfterUpdates(updates) {
    return clamp(-1 + 0.2 * Math.max(0, updates), -1, 1);
  }

  // Assume the stored mode was left before the reversal. The last eligible
  // update is one where at least one wheel still touches the ground.
  function modeAtTakeoff(lastContactUpdate) {
    return steeringAfterUpdates(lastContactUpdate) > 0.1 ? 'right' : 'left';
  }

  // Recovered target observed in the report's high-speed ice samples.
  function targetMultiplier(steeringMagnitude) {
    return 1 + Math.pow(clamp(Math.abs(steeringMagnitude)), 1.5);
  }

  // A visual interpolation through approximate points from one delayed
  // full-steering landing. This is not the game's exact recovery equation.
  function recoverySketch(elapsedMs) {
    return interpolate([[0, 1], [370, 1], [390, 1.05], [590, 2], [700, 2]],
      Math.max(0, elapsedMs));
  }

  // Prior left mode, steady neutral internal steering, continuous contact,
  // and an active icy tire-force branch. Returning left before the cutoff
  // keeps the old mode; returning after it creates a fresh mode change.
  function neutralModeAt(elapsedMs) {
    return elapsedMs < 300 ? 'left' : 'neutral';
  }

  return {
    icePoints, otherPoints, iceWeight, otherWeight, ordinaryWeight,
    icingAt, steeringAfterUpdates, modeAtTakeoff, targetMultiplier,
    recoverySketch, neutralModeAt,
  };
});
