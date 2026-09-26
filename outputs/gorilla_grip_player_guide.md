# Gorilla grip: a player's guide

How Trackmania's ice "gorilla grip" works, explained for players. The numbers come from the [research report](gorilla_grip_mechanism.md), which has the measurements and code evidence behind every claim here. They were measured on the September 2026 game build; a game update can change them.

## The short version

On icy tires the game remembers which way you are sliding, **left or right**. Every time that stored direction changes, the ice grip boost drops to its base value and a **400 ms** timer starts. Only after the timer runs out does the boost climb back.

The trick is to change the stored direction **just before a jump**, while a wheel is still on the ground. The timer then runs during the flight, and the boost is back, or nearly back, when you land. Change it on landing instead and you sit through the whole wait after touchdown.

## Setting the slide direction

- **Steer past 10% left or right while at least one wheel touches the ground.** Past +10% stores "right", past −10% stores "left". Which wheel touches doesn't matter.
- **The last wheel to leave the ground is your deadline.** In the air the stored direction can't change, whatever you steer.
- **The game's steering lags your input.** It uses a smoothed steering value that moved about 20% per 10 ms physics tick on ice in our tests. Going from full left to full right, it crosses +10% about **50–60 ms** after your input and reaches full right after about **90–100 ms**. A quick tap right before takeoff can arrive too late.
- **Small inputs never count.** Steering that stays inside ±10% can't set a direction, however long you hold it.
- **Landing steering matters too.** If your steering points the other way when the wheels touch down, the direction flips at landing and the 400 ms wait starts there.

## The grip timer

The boost runs from **1.0×** (base) to **2.0×** (full) at full steering on ice. It is a multiplier inside the game's tire-force calculation, not a speed value.

| Time since the direction changed | Grip boost |
|---|---|
| 0–400 ms | Stays at 1.0×. |
| 400–800 ms | Climbs while the car is on the ground, by +0.025 per 10 ms tick for each front wheel down. With both front wheels down it goes from 1.0× to 2.0× in 200 ms. It does not climb in the air. (Landing on rear wheels only hasn't been tested.) |
| After 800 ms | Full boost on the next ground contact, even straight after a long flight. |

What you get on landing depends on how long ago you switched:

| You land … | What happens |
|---|---|
| **Before 400 ms** | The boost stays at 1.0× until the 400 ms mark, then climbs. Still better than switching on landing: in one traced landing the switch came 70 ms before takeoff, the car touched down at 271 ms, and full grip arrived about 0.4 s after touchdown. |
| **Between 400 and 800 ms** | The boost starts low and climbs from touchdown. It is full 200 ms later with both front wheels down, or at the 800 ms mark at the latest. |
| **After 800 ms** | Full grip on the first contact. |
| **Having switched only at touchdown** | 1.0× for the first 400 ms on the ground, full grip about 0.6 s after touchdown. |

In the controlled tests, switching before takeoff instead of at touchdown meant 3.6–5.6 km/h less speed lost shortly after landing on those jumps.

**The best timing is as late as possible while the last wheel still touches.** Every millisecond between the switch and takeoff is ground time at 1.0×. If the jump is long enough (800 ms or more after the switch), switching on the last possible tick gives full grip on landing with no loss before takeoff. The [Gorilla Grip Trainer](https://github.com/Teuflum/Gorilla-Grip-Trainer) grades exactly that lead time.

## Reduced boost

- **Less steering, less boost.** The full value depends on how far you steer. At high speed on ice it measured about 2.0× at full steering, 1.72× at 80%, 1.46× at 60%, 1.25× at 40%, and 1.09× at 20%. The 10% threshold only decides the direction.
- **Centering the steering.** Between −10% and +10% the stored direction is kept for **300 ms**, then cleared (the clearing needs a wheel on the ground). Steer back the same way within 300 ms and there is no new wait, although the boost drops while you are near center. After 300 ms, steering out again counts as a new direction and restarts the 400 ms timer. After a long flight, landing with centered steering can clear the old direction.
- **Releasing gas while sliding backwards.** If the car is moving backwards relative to its nose (common mid-spin) and you release gas, the boost is held at 1.0× until you press gas again, even if it was already full. After the 800 ms mark it returns in full straight away; before that, it climbs again from 1.0×. Releasing gas while moving forwards does not trigger this. In one trace, though, the boost still fell from 2.0× to 1.0× within about 0.2 s after a forward gas release; the grip target also depends on speed, and why it dropped there has not been pinned down.

## Icy tires and surfaces

- **Tire icing is what counts.** Tires collect ice on Ice and RoadIce and lose it on other surfaces. The direction logic and the boost work on plastic as long as the tires are still icy.
- **Icing timings:** building up to full ice takes about **1.65 s** of ice contact. Losing all of it takes about **3.3 s** on the ground or **6 s** in the air.
- **Wet tires keep their ice.** Wetness sets a floor under the icing, so fully wet, fully icy tires stay icy on plastic until they dry.
- **The surface still matters.** On Ice, Snow, or RoadIce even lightly iced tires get most of the ice-style tire force: about 60% of it at 5% icing and 85% at 20%. On plastic or asphalt the same tires get far less: about 2% at 5% icing and 30% at 80%. At full icing both are 100%.
- **Clean tires on tarmac** don't show the effect at all: the boost stays at 1.0× and no direction is stored.

## Checklist

1. Have icy tires before the jump.
2. Steer clearly past 10% toward the new slide direction, early enough that the game's smoothed steering crosses it (about 50–60 ms from full opposite lock) before the last wheel leaves the ground.
3. Switch as close to takeoff as that allows.
4. Land with steering in the same direction.
5. If you release gas mid-spin while sliding backwards, press it again on landing; the boost waits for it.
