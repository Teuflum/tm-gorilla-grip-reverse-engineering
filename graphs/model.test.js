const test = require('node:test');
const assert = require('node:assert/strict');
const model = require('./model.js');

function close(actual, expected, tolerance = 1e-7) {
  assert.ok(Math.abs(actual - expected) <= tolerance, `${actual} != ${expected}`);
}

test('material curves match the measured model points and report examples', () => {
  for (const [icing, ice, other] of [
    [0, 0, 0], [0.05, 0.6, 0.01875], [0.2, 0.85, 0.075],
    [0.8, 0.9625, 0.3], [0.95, 0.990625, 0.7], [1, 1, 1],
  ]) {
    close(model.iceWeight(icing), ice);
    close(model.otherWeight(icing), other);
  }
  close(model.ordinaryWeight(0.8, 'ice'), 0.0375);
  close(model.ordinaryWeight(0.8, 'other'), 0.7);
});

test('icing rises on ice, decays on plastic and in air, and respects wetness floor', () => {
  close(model.icingAt('ice', 0, 1650, 0), 1);
  close(model.icingAt('plastic', 1, 1650, 0), 0.5);
  close(model.icingAt('plastic', 1, 3300, 0), 0);
  close(model.icingAt('air', 1, 3000, 0), 0.5);
  close(model.icingAt('air', 1, 6000, 0), 0);
  close(model.icingAt('plastic', 1, 6000, 1), 1);
  close(model.icingAt('plastic', 0.8, 6000, 0.5), 0.5);
  close(model.icingAt('plastic', 0.4, 6000, 1), 0.4);
});

test('sixth affected physics update is first to set right mode in full reversal', () => {
  close(model.steeringAfterUpdates(0), -1);
  close(model.steeringAfterUpdates(5), 0);
  close(model.steeringAfterUpdates(6), 0.2);
  close(model.steeringAfterUpdates(10), 1);
  assert.equal(model.modeAtTakeoff(5), 'left');
  assert.equal(model.modeAtTakeoff(6), 'right');
  assert.equal(model.modeAtTakeoff(10), 'right');
});

test('steering threshold and recovered force target are distinct values', () => {
  close(model.targetMultiplier(0), 1);
  close(model.targetMultiplier(0.1), 1.0316227766);
  close(model.targetMultiplier(0.2), 1.0894427191);
  close(model.targetMultiplier(0.6), 1.4647580015);
  close(model.targetMultiplier(1), 2);
});

test('illustrative recovery curve is anchored to measured landing landmarks', () => {
  close(model.recoverySketch(0), 1);
  close(model.recoverySketch(370), 1);
  close(model.recoverySketch(390), 1.05);
  close(model.recoverySketch(590), 2);
  close(model.recoverySketch(1300), 2);
});

test('neutral steering retains the old direction below 300 ms and clears it at timeout', () => {
  assert.equal(model.neutralModeAt(100), 'left');
  assert.equal(model.neutralModeAt(299), 'left');
  assert.equal(model.neutralModeAt(300), 'neutral');
  assert.equal(model.neutralModeAt(400), 'neutral');
});
