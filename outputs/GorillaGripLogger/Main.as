bool g_show = true;
bool g_recording = false;
string g_label = "right";
string g_csv = "";
string g_last_path = "";
int g_rows = 0;
int g_run = 0;
int g_last_time = -100000;
string g_status = "waiting";
int g_frames = 0;
int g_poll_counter = 0;
string g_last_auto_command = "";
string g_active_auto_command = "";
bool g_auto_saw_new_run = false;

string ReadAutoCommand() {
    string path = IO::FromStorageFolder("automation_command.txt");
    IO::File file(path, IO::FileMode::Read);
    string command = file.ReadLine();
    file.Close();
    return command;
}

void WriteAutoStatus(const string &in status) {
    string path = IO::FromStorageFolder("automation_status.txt");
    IO::File file(path, IO::FileMode::Write);
    file.Write(g_active_auto_command + " " + status + "\n");
    file.Close();
}

void CheckAutoCommand() {
    string command = ReadAutoCommand();
    if (command.Length == 0 || command == g_last_auto_command) return;
    g_last_auto_command = command;
    if (g_recording) StopTrial();
    g_active_auto_command = command;
    g_auto_saw_new_run = false;
    BeginTrial("auto_" + command);
    auto app = GetApp();
    if (app.Network is null || app.Network.PlaygroundClientScriptAPI is null) {
        WriteAutoStatus("error: no playground client API");
        StopTrial();
        return;
    }
    auto api = cast<CGamePlaygroundClientScriptAPI>(app.Network.PlaygroundClientScriptAPI);
    if (api is null) {
        WriteAutoStatus("error: wrong playground API type");
        StopTrial();
        return;
    }
    WriteAutoStatus("restarting");
    api.RequestRestartMap();
}

void RenderMenu() {
    if (UI::MenuItem("Gorilla Grip Logger")) g_show = !g_show;
}

void BeginTrial(const string &in label) {
    g_label = label;
    g_csv = "run,sample_index,time_ms,steer,gas,brake,front_speed,side_speed,ground,px,py,pz,vx,vy,vz,dirx,diry,dirz," +
        "fl_falling,fr_falling,rl_falling,rr_falling,fl_mat,fr_mat,rl_mat,rr_mat," +
        "fl_ice,fr_ice,rl_ice,rr_ice,fl_slip,fr_slip,rl_slip,rr_slip," +
        "fl_damper,fr_damper,rl_damper,rr_damper,upx,upy,upz,fl_steer_angle,fr_steer_angle," +
        "fl_wheel_rot_speed,fr_wheel_rot_speed,rl_wheel_rot_speed,rr_wheel_rot_speed\n";
    g_rows = 0;
    g_run = 0;
    g_last_time = -100000;
    g_frames = 0;
    g_status = "waiting for vehicle";
    g_recording = true;
}

void StopTrial() {
    if (!g_recording) return;
    g_recording = false;
    g_last_path = IO::FromStorageFolder("gorilla_grip_" + g_label + ".csv");
    IO::File file(g_last_path, IO::FileMode::Write);
    file.Write(g_csv);
    file.Close();
    print("Gorilla Grip Logger wrote " + g_rows + " rows to " + g_last_path);
    if (g_active_auto_command.Length > 0) {
        WriteAutoStatus("complete " + g_last_path);
        g_active_auto_command = "";
    }
}

void RenderInterface() {
    if (!g_show) return;
    if (!UI::Begin("Gorilla Grip Logger", g_show)) { UI::End(); return; }
    UI::Text("Record the same TAS branch twice, changing only pre-takeoff steering.");
    if (!g_recording) {
        if (UI::Button("Start RIGHT trial")) BeginTrial("right");
        UI::SameLine();
        if (UI::Button("Start LEFT trial")) BeginTrial("left");
    } else {
        UI::Text("Recording " + g_label + " trial; " + g_rows + " samples");
        if (UI::Button("Stop and save CSV")) StopTrial();
    }
    UI::Text("Captures the whole run, once per display frame.");
    UI::Text("Status: " + g_status + " / frames: " + g_frames);
    UI::Text("Falling: 0 air, 4 resting ground, 8 gliding ground (experimental).");
    if (g_last_path.Length > 0) UI::Text("Saved: " + g_last_path);
    UI::End();
}

void Update(float dt) {
    g_poll_counter++;
    if (g_poll_counter >= 10) { g_poll_counter = 0; CheckAutoCommand(); }
    if (!g_recording) return;
    g_frames++;
    auto app = GetApp();
    CSceneVehicleVisState@ vis = VehicleState::ViewingPlayerState();
    if (vis is null) { g_status = "no viewed vehicle"; return; }

    int t = -1;
    int startTime = -1;
    if (app.CurrentPlayground !is null && app.CurrentPlayground.GameTerminals.Length > 0) {
        CSmPlayer@ player = cast<CSmPlayer>(app.CurrentPlayground.GameTerminals[0].GUIPlayer);
        if (player !is null) {
            CSmScriptPlayer@ script = cast<CSmScriptPlayer>(player.ScriptAPI);
            if (script !is null) {
                t = script.CurrentRaceTime;
                startTime = script.StartTime;
            }
        }
    }
    if (t <= 0 && app.Network !is null && app.Network.PlaygroundClientScriptAPI !is null) {
        auto api = cast<CGamePlaygroundClientScriptAPI>(app.Network.PlaygroundClientScriptAPI);
        if (api !is null) {
            int fallbackStart = startTime >= 0 ? startTime : int(vis.RaceStartTime);
            t = api.GameTime - fallbackStart;
        }
    }
    if (t >= 0 && g_last_time >= 0 && t < g_last_time - 100) g_run++;
    if (t >= 0) g_last_time = t;
    if (g_active_auto_command.Length > 0 && t >= 0 && t < 500) g_auto_saw_new_run = true;
    g_status = "vehicle present, race time " + t;
    g_csv += "" + g_run + "," + g_rows + "," + t + "," + vis.InputSteer + "," + vis.InputGasPedal + "," +
        vis.InputBrakePedal + "," + vis.FrontSpeed + "," + VehicleState::GetSideSpeed(vis) + "," +
        (vis.IsGroundContact ? 1 : 0) + "," + vis.Position.x + "," + vis.Position.y + "," + vis.Position.z + "," +
        vis.WorldVel.x + "," + vis.WorldVel.y + "," + vis.WorldVel.z + "," +
        vis.Dir.x + "," + vis.Dir.y + "," + vis.Dir.z + "," +
        int(VehicleState::GetWheelFalling(vis, 0)) + "," + int(VehicleState::GetWheelFalling(vis, 1)) + "," +
        int(VehicleState::GetWheelFalling(vis, 2)) + "," + int(VehicleState::GetWheelFalling(vis, 3)) + "," +
        int(vis.FLGroundContactMaterial) + "," + int(vis.FRGroundContactMaterial) + "," +
        int(vis.RLGroundContactMaterial) + "," + int(vis.RRGroundContactMaterial) + "," +
        vis.FLIcing01 + "," + vis.FRIcing01 + "," + vis.RLIcing01 + "," + vis.RRIcing01 + "," +
        vis.FLSlipCoef + "," + vis.FRSlipCoef + "," + vis.RLSlipCoef + "," + vis.RRSlipCoef + "," +
        vis.FLDamperLen + "," + vis.FRDamperLen + "," + vis.RLDamperLen + "," + vis.RRDamperLen + "," +
        vis.Up.x + "," + vis.Up.y + "," + vis.Up.z + "," +
        vis.FLSteerAngle + "," + vis.FRSteerAngle + "," +
        vis.FLWheelRotSpeed + "," + vis.FRWheelRotSpeed + "," +
        vis.RLWheelRotSpeed + "," + vis.RRWheelRotSpeed + "\n";
    g_rows++;
    if (g_active_auto_command.Length > 0 && g_auto_saw_new_run && t >= 13500) StopTrial();
}
