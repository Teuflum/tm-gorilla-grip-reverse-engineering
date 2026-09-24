// Gorilla Grip Rater. Original HUD and transition logic for icy-tire airtime.
// Exact fields are read only after the current physics car is validated.

[Setting category="Display" name="Show arcade HUD"]
bool S_Show = true;
[Setting category="Display" name="Hide with game UI"]
bool S_HideWithUI = true;
[Setting category="Display" name="Horizontal position" min=0 max=1]
float S_X = 0.5f;
[Setting category="Display" name="Vertical position" min=0 max=1]
float S_Y = 0.78f;
[Setting category="Display" name="Scale" min=0.5 max=2]
float S_Scale = 1.0f;
[Setting category="Rating" name="Minimum average tire icing" min=0 max=1]
float S_MinIcing = 0.65f;
[Setting category="Rating" name="Minimum flight (ms)" min=50 max=1000]
int S_MinFlight = 100;
[Setting category="Rating" name="Minimum speed (km/h)" min=0 max=300]
int S_MinSpeed = 50;
[Setting category="Rating" name="Force for GOOD" min=1 max=2]
float S_GoodForce = 1.40f;
[Setting category="Rating" name="Force for GREAT" min=1 max=2]
float S_GreatForce = 1.75f;
[Setting category="Rating" name="Force for PERFECT" min=1 max=2]
float S_PerfectForce = 1.95f;
[Setting category="Rating" name="Show provisional grades when exact physics is unavailable"]
bool S_Provisional = true;

const float GATE = 0.1f;
const float TAU = 6.2831853f;
int g_font = -1;
bool g_hasCar = false;
bool g_exact = false;
bool g_ground = false;
bool g_wasGround = false;
bool g_air = false;
bool g_eligible = false;
bool g_pendingLanding = false;
bool g_takeoffExact = false;
bool g_landingExact = false;
bool g_haveTime = false;
int g_raceTime = -1;
int g_lastRaceTime = -1;
int g_takeoffTime = -1;
int g_landingTime = -1;
int g_flightMs = 0;
int g_landingDeadline = -1;
int g_takeoffMode = 0;
int g_mode = 0;
int g_estMode = 0;
int g_neutralTime = -1;
int g_combo = 0;
int g_bestCombo = 0;
int g_score = 0;
int g_prevScore = 0;
int g_prevBest = 0;
int g_successes = 0;
int g_misses = 0;
int g_prevSuccesses = 0;
int g_prevMisses = 0;
float g_rawSteer = 0;
float g_steer = 0;
float g_estSteer = 0;
float g_icing = 0;
float g_force = 1;
float g_speed = 0;
float g_airSpin = 0;
float g_lastYaw = 0;
float g_takeoffIcing = 0;
float g_landingForce = 1;
float g_landingSteer = 0;
uint64 g_vehicle = 0;
bool g_supportedBuild = false;
uint64 g_resultAt = 0;
string g_result = "";
string g_reason = "";
string g_source = "ESTIMATE";

void Main() {
    g_font = nvg::LoadFont("DroidSans-Bold.ttf");
    uint64 base = Dev::BaseAddress();
    uint peOffset = Dev::SafeReadUint32(base + 0x3c);
    g_supportedBuild = peOffset > 0x40 && peOffset < 0x1000 &&
        Dev::SafeReadUint32(base + peOffset + 8) == 0x6980d607 &&
        Dev::SafeReadUint32(base + peOffset + 24 + 56) == 0x2cba000;
}

void RenderMenu() {
    if (UI::MenuItem("Gorilla Grip Rater", "", S_Show)) S_Show = !S_Show;
}

int Direction(float value) {
    if (value > GATE) return 2;
    if (value < -GATE) return 1;
    return 0;
}

string DirectionName(int direction) {
    if (direction == 1) return "LEFT";
    if (direction == 2) return "RIGHT";
    return "NEUTRAL";
}

bool ReadExact(CSceneVehicleVisState@ vis) {
    if (!g_supportedBuild) return false;
    auto app = GetApp();
    if (app is null || app.CurrentPlayground is null || app.CurrentPlayground.GameTerminals.Length == 0) return false;
    CSmPlayer@ player = cast<CSmPlayer>(app.CurrentPlayground.GameTerminals[0].GUIPlayer);
    if (player is null) return false;
    g_vehicle = Dev::GetOffsetUint64(player, 0x1118);
    if (g_vehicle < 0x10000) return false;
    if (Dev::SafeReadUint32(g_vehicle + 0x380) != 4) return false;
    uint64 model = Dev::SafeReadUint64(g_vehicle + 0x88);
    if (model < 0x10000) return false;
    vec3 pos = Dev::SafeReadVec3(g_vehicle + 0x538);
    if ((pos - vis.Position).Length() > 4.0f) return false;
    float raw = Dev::SafeReadFloat(g_vehicle + 0xa0);
    if (Math::Abs(raw - vis.InputSteer) > 0.25f) return false;
    float smooth = Dev::SafeReadFloat(g_vehicle + 0x1430);
    float force = Dev::SafeReadFloat(g_vehicle + 0x14dc);
    uint8 mode = Dev::SafeReadUint8(g_vehicle + 0x14e5);
    if (smooth < -1.001f || smooth > 1.001f || force < 0.95f || force > 2.1f || mode > 2) return false;
    g_steer = smooth;
    g_force = force;
    g_mode = int(mode);
    return true;
}

int RaceTime(CSceneVehicleVisState@ vis) {
    auto app = GetApp();
    int t = -1;
    int start = int(vis.RaceStartTime);
    if (app !is null && app.CurrentPlayground !is null && app.CurrentPlayground.GameTerminals.Length > 0) {
        CSmPlayer@ player = cast<CSmPlayer>(app.CurrentPlayground.GameTerminals[0].GUIPlayer);
        if (player !is null) {
            CSmScriptPlayer@ script = cast<CSmScriptPlayer>(player.ScriptAPI);
            if (script !is null) {
                t = script.CurrentRaceTime;
                start = script.StartTime;
            }
        }
    }
    if (t <= 0 && app !is null && app.Network !is null && app.Network.PlaygroundClientScriptAPI !is null) {
        auto api = cast<CGamePlaygroundClientScriptAPI>(app.Network.PlaygroundClientScriptAPI);
        if (api !is null) t = api.GameTime - start;
    }
    return t;
}

void EndRun() {
    if (g_successes + g_misses > 0) {
        g_prevScore = g_score;
        g_prevBest = g_bestCombo;
        g_prevSuccesses = g_successes;
        g_prevMisses = g_misses;
    }
    g_combo = 0;
    g_bestCombo = 0;
    g_score = 0;
    g_successes = 0;
    g_misses = 0;
    g_air = false;
    g_pendingLanding = false;
    g_wasGround = false;
    g_result = "";
    g_estSteer = 0;
    g_estMode = 0;
    g_neutralTime = -1;
}

void StepEstimate(int t, bool grounded) {
    float delta = g_rawSteer - g_estSteer;
    g_estSteer += Math::Clamp(delta, -0.2f, 0.2f);
    if (!grounded || g_icing <= 0) return;
    int direction = Direction(g_estSteer);
    if (direction != 0) {
        g_estMode = direction;
        g_neutralTime = -1;
    } else if (g_estMode != 0) {
        if (g_neutralTime < 0) g_neutralTime = t;
        else if (t - g_neutralTime >= 300) g_estMode = 0;
    }
}

void ShowVerdict(const string &in label, const string &in reason, bool success, int points) {
    g_result = label;
    g_reason = reason;
    g_resultAt = Time::Now;
    if (success) {
        g_combo++;
        g_successes++;
        g_bestCombo = Math::Max(g_bestCombo, g_combo);
        g_score += points * Math::Min(g_combo, 8);
    } else {
        g_combo = 0;
        g_misses++;
    }
    print("Gorilla Grip Rater verdict at " + g_raceTime + "ms: " + label +
        " | " + reason + " | takeoff mode " + g_takeoffMode +
        " | landing steer " + g_landingSteer + " | landing force " +
        g_landingForce + " | exact " + (g_takeoffExact && g_landingExact));
}

void GradeLanding() {
    int landingDirection = Direction(g_steer);
    if (landingDirection == 0) return;
    g_pendingLanding = false;
    bool provisional = !g_takeoffExact || !g_landingExact;
    if (provisional && !S_Provisional) return;
    string marker = provisional ? " ~" : "";
    if (g_takeoffMode == 0) {
        ShowVerdict("NO SET" + marker, "No direction stored before takeoff", false, 0);
    } else if (g_takeoffMode != landingDirection) {
        ShowVerdict("WRONG WAY" + marker, "Stored " + DirectionName(g_takeoffMode) + ", landed " + DirectionName(landingDirection), false, 0);
    } else if (provisional) {
        ShowVerdict("ALIGNED ~", "Steering estimate only; tire force unverified", true, 50);
    } else if (g_landingForce >= S_PerfectForce) {
        int spinBonus = int(g_airSpin / TAU) * 50;
        string bonus = spinBonus > 0 ? "  |  SPIN +" + spinBonus : "";
        ShowVerdict("PERFECT", "Force " + Text::Format("%.2f", g_landingForce) + "x just after landing" + bonus, true, 150 + spinBonus);
    } else if (g_landingForce >= S_GreatForce) {
        ShowVerdict("GREAT", "Fast force " + Text::Format("%.2f", g_landingForce) + "x", true, 100);
    } else if (g_landingForce >= S_GoodForce) {
        ShowVerdict("GOOD", "Force " + Text::Format("%.2f", g_landingForce) + "x", true, 60);
    } else {
        ShowVerdict("DELAYED", "Force only " + Text::Format("%.2f", g_landingForce) + "x after landing", false, 0);
    }
}

void Update(float dt) {
    auto vis = VehicleState::ViewingPlayerState();
    if (vis is null) {
        if (g_hasCar) EndRun();
        g_hasCar = false;
        g_exact = false;
        return;
    }
    g_hasCar = true;
    int t = RaceTime(vis);
    if (t < 0) return;
    if (g_lastRaceTime >= 0 && t < g_lastRaceTime - 50) EndRun();
    int elapsed = g_lastRaceTime < 0 ? 10 : Math::Clamp(t - g_lastRaceTime, 0, 200);
    g_lastRaceTime = t;
    g_raceTime = t;
    g_rawSteer = Math::Clamp(vis.InputSteer, -1.0f, 1.0f);
    g_icing = (vis.FLIcing01 + vis.FRIcing01 + vis.RLIcing01 + vis.RRIcing01) * 0.25f;
    g_speed = vis.WorldVel.Length() * 3.6f;
    g_ground = vis.IsGroundContact;

    for (int i = 0; i < elapsed / 10; i++) StepEstimate(t - elapsed + (i + 1) * 10, g_ground);
    g_exact = ReadExact(vis);
    if (g_exact) {
        g_source = "EXACT PHYSICS";
    } else {
        g_steer = g_estSteer;
        g_mode = g_estMode;
        g_force = 1.0f;
        g_source = "ESTIMATE";
    }

    float yaw = Math::Atan2(vis.Dir.x, vis.Dir.z);
    if (g_air) {
        float turn = yaw - g_lastYaw;
        if (turn > Math::PI) turn -= TAU;
        if (turn < -Math::PI) turn += TAU;
        g_airSpin += Math::Abs(turn);
    }
    g_lastYaw = yaw;

    if (g_wasGround && !g_ground) {
        // A brief touchdown followed by another hop is not a settled landing.
        g_pendingLanding = false;
        g_air = true;
        g_takeoffTime = t;
        g_takeoffMode = g_mode;
        g_takeoffExact = g_exact;
        g_takeoffIcing = g_icing;
        g_airSpin = 0;
        g_eligible = g_icing >= S_MinIcing && g_speed >= float(S_MinSpeed);
        print("Gorilla Grip Rater takeoff " + t + "ms, mode " + g_takeoffMode +
            ", icing " + g_icing + ", speed " + g_speed + ", eligible " + g_eligible);
    }
    if (g_air && !g_wasGround && g_ground) {
        g_air = false;
        g_landingTime = t;
        g_flightMs = t - g_takeoffTime;
        g_landingExact = false;
        g_landingForce = g_force;
        g_landingSteer = g_steer;
        g_pendingLanding = g_eligible && g_flightMs >= S_MinFlight;
        g_landingDeadline = t + 150;
        print("Gorilla Grip Rater landing " + t + "ms, air " + g_flightMs +
            "ms, steer " + g_landingSteer + ", force " + g_landingForce +
            ", pending " + g_pendingLanding);
    }
    if (g_pendingLanding && t - g_landingTime >= 30) {
        g_landingExact = g_exact;
        g_landingForce = g_force;
        g_landingSteer = g_steer;
        if (Direction(g_steer) != 0) GradeLanding();
        else if (t >= g_landingDeadline) {
            g_pendingLanding = false;
            bool finalExact = g_takeoffExact && g_exact;
            if (finalExact || S_Provisional) {
                ShowVerdict(finalExact ? "NO STEER" : "NO STEER ~",
                    "Steering stayed inside the 10% gate", false, 0);
            }
        }
    }
    g_wasGround = g_ground;
}

vec4 C(float r, float g, float b, float a = 1.0f) { return vec4(r, g, b, a); }

void Box(float x, float y, float w, float h, float radius, const vec4 &in color) {
    nvg::BeginPath();
    nvg::RoundedRect(x, y, w, h, radius);
    nvg::FillColor(color);
    nvg::Fill();
}

void Txt(float x, float y, const string &in value, float size, const vec4 &in color, int align) {
    nvg::FontSize(size);
    nvg::TextAlign(align);
    nvg::FillColor(color);
    nvg::Text(x, y, value);
}

void Render() {
    if (!S_Show || !g_hasCar || g_raceTime < 0) return;
    if (S_HideWithUI && !UI::IsGameUIVisible()) return;
    float s = S_Scale * float(Display::GetHeight()) / 1080.0f;
    float w = 500 * s;
    float h = 231 * s;
    float x = S_X * Display::GetWidth() - w * 0.5f;
    float y = S_Y * Display::GetHeight() - h * 0.5f;
    int L = nvg::Align::Left | nvg::Align::Middle;
    int R = nvg::Align::Right | nvg::Align::Middle;
    int M = nvg::Align::Center | nvg::Align::Middle;
    if (g_font >= 0) nvg::FontFace(g_font);
    Box(x + 3*s, y + 5*s, w, h, 16*s, C(0, 0, 0, 0.35f));
    Box(x, y, w, h, 16*s, C(0.025f, 0.035f, 0.09f, 0.91f));
    Box(x, y, 6*s, h, 3*s, C(0.0f, 0.92f, 0.86f));
    Box(x + 16*s, y + 16*s, 6*s, 6*s, 3*s, C(0.0f, 1.0f, 0.86f));
    Txt(x + 30*s, y + 20*s, "GORILLA GRIP", 17*s, C(0.91f, 0.98f, 1), L);
    Txt(x + w - 17*s, y + 20*s, g_source, 11*s, g_exact ? C(0.1f, 1, 0.73f) : C(1, 0.72f, 0.2f), R);

    float steerPct = g_steer * 100.0f;
    Txt(x + 20*s, y + 65*s, Text::Format("%+.1f", steerPct) + "%", 38*s, C(1, 1, 1), L);
    Txt(x + 205*s, y + 64*s, "INTERNAL STEER", 12*s, C(0.52f, 0.65f, 0.72f), L);
    Txt(x + w - 20*s, y + 63*s, DirectionName(g_mode), 20*s,
        g_mode == 2 ? C(0.05f, 0.95f, 0.89f) : (g_mode == 1 ? C(1, 0.38f, 0.79f) : C(0.55f, 0.62f, 0.72f)), R);

    float mx = x + 21*s;
    float my = y + 91*s;
    float mw = (w/s - 42)*s;
    Box(mx, my, mw, 16*s, 8*s, C(0.08f, 0.15f, 0.22f));
    Box(mx + mw * 0.45f, my, mw * 0.10f, 16*s, 0, C(0.25f, 0.28f, 0.36f));
    Box(mx + mw*0.45f - s, my - 4*s, 2*s, 24*s, 0, C(1, 0.38f, 0.79f));
    Box(mx + mw*0.55f - s, my - 4*s, 2*s, 24*s, 0, C(0.0f, 0.95f, 0.85f));
    Box(mx + Math::Clamp((g_steer + 1)*0.5f, 0.0f, 1.0f)*mw - 3*s, my - 5*s, 6*s, 26*s, 3*s, C(1, 1, 1));
    Txt(mx, my + 29*s, "LEFT GATE", 10*s, C(1, 0.38f, 0.79f), L);
    Txt(mx + mw, my + 29*s, "RIGHT GATE", 10*s, C(0.0f, 0.95f, 0.85f), R);

    string phase = g_air ? "AIR  " + ((g_raceTime - g_takeoffTime)) + " ms" : "GROUND";
    Txt(x + 20*s, y + 151*s, phase, 15*s, C(0.89f, 0.94f, 1), L);
    Txt(x + 195*s, y + 151*s, "ICE " + Text::Format("%.0f", g_icing*100) + "%", 13*s, C(0.43f, 0.78f, 1), L);
    Txt(x + w - 20*s, y + 151*s, g_exact ? "FORCE " + Text::Format("%.2f", g_force) + "x" : "FORCE --", 15*s, C(1, 0.85f, 0.42f), R);
    Box(x + 17*s, y + 170*s, w - 34*s, 1*s, 0, C(0.23f, 0.35f, 0.47f));
    Txt(x + 20*s, y + 189*s, "COMBO  x" + g_combo, 14*s, C(1, 0.79f, 0.28f), L);
    Txt(x + 205*s, y + 189*s, "SCORE  " + g_score, 14*s, C(0.9f, 0.96f, 1), L);
    Txt(x + w - 20*s, y + 189*s, "BEST  x" + g_bestCombo, 12*s, C(0.55f, 0.65f, 0.78f), R);
    Txt(x + 20*s, y + 215*s,
        "LAST RUN  " + g_prevScore + " pts   " + g_prevSuccesses + " hits / " +
        g_prevMisses + " misses   best x" + g_prevBest,
        11*s, C(0.49f, 0.58f, 0.71f), L);

    if (g_result.Length > 0 && Time::Now - g_resultAt < 2600) {
        float fade = 1.0f - Math::Clamp(float(Time::Now - g_resultAt - 1800) / 800.0f, 0.0f, 1.0f);
        float bump = 1.0f + 0.12f * Math::Max(0.0f, 1.0f - float(Time::Now - g_resultAt) / 230.0f);
        vec4 accent = g_result.StartsWith("PERFECT") ? C(1, 0.84f, 0.26f, fade) :
            (g_result.StartsWith("GREAT") || g_result.StartsWith("GOOD") || g_result.StartsWith("ALIGNED") ? C(0, 1, 0.84f, fade) : C(1, 0.31f, 0.6f, fade));
        Box(x + 20*s, y - 65*s, w - 40*s, 58*s, 12*s, C(0.025f, 0.035f, 0.09f, 0.88f*fade));
        Txt(x + w*0.5f, y - 43*s, g_result, 28*s*bump, accent, M);
        Txt(x + w*0.5f, y - 17*s, g_reason, 11*s, C(0.9f, 0.95f, 1, fade), M);
    }
}
