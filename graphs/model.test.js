const test = require('node:test');
const assert = require('node:assert/strict');
const model = require('./model.js');
const flick = require('./plastic-flick-data.js');

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

test('speed across the front wheels scales the recovered target', () => {
  close(model.speedCurve(36), 0);
  close(model.speedCurve(72), 0.5);
  close(model.speedCurve(108), 1);
  close(model.speedCurve(200), 1);
  close(model.sidewaysSpeed(100, 90), 100);
  close(model.sidewaysSpeed(100, 0), 0);
  // Full steering, from the table in outputs/speed_force_curve.md.
  for (const [angle, speed, target] of [
    [45, 50, 1], [45, 75, 1.24], [45, 100, 1.48], [45, 150, 1.97], [45, 200, 2],
    [90, 50, 1.19], [90, 100, 1.89], [30, 150, 1.54], [15, 200, 1.22], [0, 250, 1],
  ]) close(model.targetMultiplier(1, model.sidewaysSpeed(speed, angle)), target, 0.006);
  // A straight run or a 90° slide at full steering: boost from ~51, full from ~153 km/h.
  close(model.targetMultiplier(1, model.sidewaysSpeed(50.9, 45)), 1, 0.001);
  close(model.targetMultiplier(1, model.sidewaysSpeed(152.8, 45)), 2, 0.001);
  close(model.targetMultiplier(0.6, model.sidewaysSpeed(100, 45)), 1 + 0.4647580015 * (100 * Math.SQRT1_2 - 36) / 72);
});

test('surface factor turns the steered wheels less on plastic at the same icing', () => {
  close(model.wheelAngle(1, 1, true), 45);
  close(model.wheelAngle(1, 1, false), 45);
  close(model.wheelAngle(1, 0.84, true), 43.65);
  close(model.wheelAngle(1, 0.84, false), 45 * (0.3 + 0.04 / 0.15 * 0.4));
  close(model.wheelAngle(0.5, 0.84, true), 21.825);
  // Wheels pointing along the travel direction get no boost.
  close(model.slideTarget(200, 43.65, 43.65, 1), 1);
  close(model.slideTarget(200, 90, 45, 1), 2);
});

test('the plastic flick replay follows the material-selected surface factor', () => {
  const predict = (row, byMaterial) => model.slideTarget(row.speedKmh, row.slipDeg,
    model.wheelAngle(1, row.icing, byMaterial ? row.iceFamily : true), 1);
  let byMaterial = 0, iceAlways = 0;
  for (const row of flick) {
    byMaterial = Math.max(byMaterial, Math.abs(predict(row, true) - row.force));
    iceAlways = Math.max(iceAlways, Math.abs(predict(row, false) - row.force));
  }
  assert.ok(byMaterial < 0.04, `material-selected error ${byMaterial}`);
  assert.ok(iceAlways > 0.8,`ice-curve error ${iceAlways}`);
  // All four wheels on plastic until the front-left wheel reaches RoadIce at 8282 ms.
  const plastic = flick.filter(row => !row.iceFamily).map(row => row.t);
  assert.deepEqual([plastic[0], plastic.at(-1)], [7770, 8271]);
  assert.equal(flick.find(row => row.t === 8282).force, 1.013);
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
